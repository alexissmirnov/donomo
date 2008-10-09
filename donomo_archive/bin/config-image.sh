#!/bin/sh -e

set -x

source $(dirname $0)/parse-args.sh "$@"

#
# Check consistency of passwd and group files and make appropriate corrections
#

authconfig --enableshadow --useshadow --enablemd5 --updateall

#
# Set default root password on instance;
#
passwd root

cat > /etc/hosts <<EOF
127.0.0.1 localhost localhost.localdomain
EOF

cat > /etc/sysconfig/network <<EOF
NETWORKING=yes
HOSTNAME=localhost.localdomain
EOF

cat > /etc/sysconfig/network-scripts/ifcfg-eth0 <<EOF
DEVICE=eth0
BOOTPROTO=dhcp
ONBOOT=yes
TYPE=Ethernet
USERCTL=yes
PEERDNS=yes
IPV6INIT=no
EOF

#
# sshd config
#

# Allow only key-based root logins and don't attempt reverse DNS lookups upon
# connections.
#
sed -r -i 's/^PermitRootLogin\s+[a-zA-Z\-\_]+/PermitRootLogin without-password/g' /etc/ssh/sshd_config
sed -r -i 's/^PasswordAuthentication\s+[a-zA-Z\-\_]+/PasswordAuthentication no/g' /etc/ssh/sshd_config
sed -r -i 's/^.*UseDNS\s+[a-zA-Z\-\_]+/UseDNS no/g' /etc/ssh/sshd_config
sed -r -i 's/^.*ClientAliveInterval\s+[0-9]+/ClientAliveInterval 60/g' /etc/ssh/sshd_config
sed -r -i 's/^.*ClientAliveCountMax\s+[0-9]+/ClientAliveCountMax 240/g' /etc/ssh/sshd_config

# Create and populate /root/.ssh directory
#
mkdir -p /root/.ssh
if [[ -f /tmp/updates/authorized_keys ]]
then
    /bin/cp -f /tmp/updates/authorized_keys /root/.ssh/
fi
touch /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/*

#
# Document /var/spool/cron/root crontab file for root. (include fields
# definition)
# and set proper default crontab env. variables
#

cat > /var/spool/cron/root << EOF
######################################################################
# Crontab Syntax
#
# field          allowed values
# -----          --------------
# minute         0-59
# hour           0-23
# day of month   1-31
# month          1-12 (or names, see below)
# day of week    0-7 (0 or 7 is Sun, or use names)
#
# A field may be an asterisk (*), which always stands for "first-last".
#
# See man 5 crontab for all details.
#
########################################################################
#
# Default environment for cronjobs
#
SHELL=/bin/sh
MAILTO=root
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/usr/local/pi/bin
HOME=/root
EOF

# Change local time to GMT
#
mv /etc/localtime /etc/localtime.orig
ln -sf /usr/share/zoneinfo/GMT0 /etc/localtime

#
# Boot environment
#
set +e

chkconfig haldaemon on
chkconfig iptables on
chkconfig network on
chkconfig sshd on
chkconfig syslog on
chkconfig sysstat on
chkconfig psacct on

if [[ $multicore -eq 1 ]]
then
    chkconfig irqbalance on
else
    chkconfig irqbalance off
fi

#
# Disable unnecesary startup daemons
#

chkconfig ConsoleKit off
chkconfig NetworkManager off
chkconfig NetworkManagerDispatcher off
chkconfig acpid off
chkconfig anacron off
chkconfig apmd off
chkconfig atd off
chkconfig auditd off
chkconfig autofs off
chkconfig avahi-daemon off
chkconfig avahi-dnsconfd off
chkconfig bluetooth off
chkconfig cpuspeed off
chkconfig crond off
chkconfig cups off
chkconfig dc_client off
chkconfig dc_server off
chkconfig dhcdbd off
chkconfig diskdump off
chkconfig dovecot off
chkconfig dund off
chkconfig firstboot off
chkconfig gpm off
chkconfig hidd off
chkconfig httpd off
chkconfig ip6tables off
chkconfig irda off
chkconfig jexec off
chkconfig kudzu off
chkconfig libvirtd off
chkconfig lm_sensors off
chkconfig mcstrans off
chkconfig mdmonitor off
chkconfig mdmpd off
chkconfig messagebus off
chkconfig multipathd off
chkconfig munin-node off
chkconfig mysqld off
chkconfig named off
chkconfig nasd off
chkconfig netfs off
chkconfig netplugd off
chkconfig nfs off
chkconfig nfslock off
chkconfig nrpe off
chkconfig nscd off
chkconfig ntpd off
chkconfig pand off
chkconfig pcscd off
chkconfig portmap off
chkconfig puppet off
chkconfig rdisc off
chkconfig readahead_early off
chkconfig readahead_later off
chkconfig restorecond off
chkconfig rpcbind off
chkconfig rpcgssd off
chkconfig rpcidmapd off
chkconfig rpcsvcgssd off
chkconfig saslauthd off
chkconfig sendmail off
chkconfig smartd off
chkconfig snmpd off
chkconfig snmptrapd off
chkconfig spamassassin off
chkconfig squid off
chkconfig tux off
chkconfig winbind off
chkconfig wpa_supplicant off
chkconfig xend off
chkconfig xendomains off
chkconfig xfs off
chkconfig ypbind off
chkconfig yum-updatesd off

set -e

#
# Disable SELinux
#
mkdir -p /etc/selinux
cat > /etc/selinux/config <<EOF
SELINUX=disabled
SELINUXTYPE=targeted
EOF

ln -sf /etc/selinux/config /etc/sysconfig/selinux


#
# Enable Xen native memory addressing for glibc .
#

cat  > /etc/ld.so.conf.d/xen-libc6.conf <<EOF
hwcap 0 nosegneg
EOF

ldconfig

#
# Start setting up iptables
#

cat > /etc/sysconfig/iptables << EOF
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -i lo -j ACCEPT
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
EOF


#
# Start setting up SELinux
#

cat > /etc/sysconfig/system-config-securitylevel << EOF
# Configuration file for system-config-securitylevel
--enabled
--port=22:tcp
EOF

if [[ $(( database + application + processors )) -gt 0 ]]
then
    useradd donomo

    mv /tmp/updates/donomo_archive/* /home/donomo/
    chown -R donomo:donomo /home/donomo
    chown -R donomo:donomo /home/donomo/.*
    find /home/donomo -type d -print0 | xargs -0 chmod 750
    find /home/donomo -type f -print0 | xargs -0 chmod 640
    chmod 750 /home/donomo/bin/*
    mkdir -p /var/lib/donomo/cache
    mkdir -p /var/log/donomo
    mkdir -p /var/run/donomo
    chown -R donomo:donomo /var/lib/donomo
    chown -R donomo:donomo /var/log/donomo
    chown -R donomo:donomo /var/run/donomo

    mkdir -p /root/.donomo
    /bin/cp -f /tmp/updates/aws.sh /root/.donomo/aws.sh
    cat > /root/.donomo/db_pwd_donomo.sh <<EOF
export DATABASE_PASSWORD=310711f3249542dfa52d9737533771b9
EOF
fi

if [[ $database -eq 1 ]]
then

    # --- IP Tables ---
    cat >> /etc/sysconfig/iptables << EOF
-A INPUT -m state --state NEW -m tcp -p tcp --dport 3306 -j ACCEPT
EOF

    # --- SE Linus ---
    cat >> /etc/sysconfig/system-config-securitylevel << EOF
--port=3306
EOF

    # --- Root's DB Password ---
    cat > /root/.donomo/db_pwd_root.sh <<EOF
export ROOT_PASSWORD=259053d112344fb09b4e8ddb83779803
EOF

    # --- Use Transactional Tables ---
    /bin/cp -f /home/donomo/mysqld/my.cnf /etc/my.cnf
    chown root:root /etc/my.cnf
    chmod 644 /etc/my.cnf

    # --- Init Script ---
    /bin/cp -f /home/donomo/init.d/donomo-dbinit /etc/init.d/
    chown root:root /etc/init.d/donomo-dbinit
    chmod 750 /etc/init.d/donomo-dbinit

    # --- Start services automatically ---
    touch /etc/sysconfig/donomo.db
    chkconfig mysqld on
    chkconfig donomo-dbinit on
fi

if [[ $application -eq 1 ]]
then
    # --- IP Tables ---
    cat >> /etc/sysconfig/iptables << EOF
-A INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 443 -j ACCEPT
EOF

    # --- SE Linux ---
    cat >> /etc/sysconfig/system-config-securitylevel << EOF
--port=80
--port=443
EOF

    # --- Init Script ---
    /bin/cp -f /home/donomo/init.d/donomo-app /etc/init.d/
    chown root:root /etc/init.d/donomo-app
    chmod 750 /etc/init.d/donomo-app

    # --- Config Files ---
    /bin/cp -f /home/donomo/nginx/*.conf /etc/nginx/
    chown root:root /etc/nginx/*
    chmod 644 /etc/nginx/*

    path=/home/donomo/lib/donomo/archive/media
    find $path -type f -print0 | xargs -0 chmod 644
    find $path -type d -print0 | xargs -0 chmod 755
    until [[ "$path" = "/home" ]]
    do
        chmod o+x $path
        path=$(dirname $path)
    done

    mkdir -p /var/lib/nginx/empty

    # --- Turn on Services ---
    chkconfig nginx on
    chkconfig donomo-app on
fi

if [[ $processors -eq 1 ]]
then
    # --- Init Script ---
    /bin/cp -f /home/donomo/init.d/donomo-procs /etc/init.d/
    chown root:root /etc/init.d/donomo-procs
    chmod 750 /etc/init.d/donomo-procs

    # -- Turn on Services ---
    chkconfig donomo-procs on
fi


if [[ $solr -eq 1 ]]
then
    cat >> /etc/sysconfig/iptables << EOF
-A INPUT -m state --state NEW -m tcp -p tcp --dport 8983 -j ACCEPT
EOF

    cat >> /etc/sysconfig/system-config-securitylevel << EOF
--port=8983
EOF
fi


cat >> /etc/sysconfig/iptables << EOF
-A INPUT -j REJECT --reject-with icmp-host-prohibited
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
COMMIT
EOF

chmod 600 /etc/sysconfig/iptables
chmod 644 /etc/sysconfig/system-config-securitylevel

/bin/cp -f /home/donomo/init.d/rc.local /etc/init.d
chown root:root /etc/init.d/rc.local
chmod 754 /etc/init.d/rc.local

#
# Clean up /home/donomo
#

#rm -rf /home/donomo/init.d
#rm -rf /home/donomo/nginx
#rm -rf /home/donomo/mysqld
#rm -rf /home/donomo/solr


#
# Clean the /root directory and your shell history and exit from the image
#
rm -rf /root/*
chown -R root:root /root/.donomo
chmod 700 /root/.donomo
chmod 600 /root/.donomo/*

echo -n '' > /root/.bash_history
