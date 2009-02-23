#!/bin/sh -e

set -x

source $(dirname $0)/parse-args.sh "$@"

source_tree=/tmp/updates/trunk

#
# Check consistency of passwd and group files and make appropriate corrections
#

authconfig --enableshadow --useshadow --enablemd5 --updateall

#
# Set default root password on instance;
#
chpasswd <<EOF
root:$(uuidgen)
EOF

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
cat ${source_tree}/xen/ssh/* > /root/.ssh/authorized_keys
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
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin
HOME=/root
EOF

if [[ $processors -gt $(( database + application + solr )) ]]
then
    cat >> /var/spool/cron/root <<EOF
*/5 * * * * service donomo-procs prune
EOF

if [[ $database -gt 0 ]]
then
    cat >> /var/spool/cron/root <<EOF
*/5 * * * * service donomo-procs spawn
EOF

# Change local time to GMT
#
mv /etc/localtime /etc/localtime.orig
ln -sf /usr/share/zoneinfo/GMT0 /etc/localtime

ln -sf /opt/rightscale/etc/init.d/rightscale /etc/init.d/rightscale
chmod +x /opt/rightscale/etc/init.d/rightscale
chmod +x /etc/init.d/rightscale

echo "Modifying Services"


#
# Boot environment
#
set +e

chkconfig rightscale on
chkconfig getsshkey on
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

mkdir -p /root/.donomo

if [[ $ec2 -eq 1 ]]
then
    /bin/cp -f ${source_tree}/xen/aws/* /root/.donomo/
fi

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

if [[ $solr -eq 1 ]]
then
    useradd solr

    chpasswd <<EOF
solr:$(uuidgen)
EOF

    /bin/cp -rf ${source_tree}/donomo_archive/solr/* /home/solr/

    mkdir -p /var/lib/solr
    mkdir -p /var/log/solr
    mkdir -p /var/run/solr

    /bin/rm -rf /home/solr/logs
    ln -s /var/log/solr /home/solr/logs

    chown -R solr:solr /home/solr
    chown -R solr:solr /var/lib/solr
    chown -R solr:solr /var/log/solr
    chown -R solr:solr /var/run/solr

    cat >> /etc/sysconfig/iptables << EOF
-A INPUT -m state --state NEW -m tcp -p tcp --dport 8983 -j ACCEPT
EOF

    cat >> /etc/sysconfig/system-config-securitylevel << EOF
--port=8983
EOF

    /bin/cp -f ${source_tree}/donomo_archive/init.d/solr /etc/init.d/solr
    chown root:root /etc/init.d/solr
    chmod 750 /etc/init.d/solr

    chkconfig solr on
fi


if [[ $(( database + application + processors )) -gt 0 ]]
then
    useradd donomo

    chpasswd <<EOF
donomo:$(uuidgen)
EOF

    /bin/cp -rf ${source_tree}/donomo_archive/* /home/donomo/
    find /home/donomo -type d -print0 | xargs -0 chmod 750
    find /home/donomo -type f -print0 | xargs -0 chmod 640
    chmod 750 /home/donomo/bin/*
    mkdir -p /var/lib/donomo/cache
    mkdir -p /var/log/donomo
    mkdir -p /var/run/donomo
    chown -R donomo:donomo /home/donomo
    chown -R donomo:donomo /var/lib/donomo
    chown -R donomo:donomo /var/log/donomo
    chown -R donomo:donomo /var/run/donomo

    /bin/cp -f ${source_tree}/xen/aws/aws.sh /root/.donomo/aws.sh
    cat > /root/.donomo/db_pwd_donomo.sh <<EOF
export DATABASE_PASSWORD=146eb0938ee346ad8b35d6e1397fe82d
export KEY_PREFIX=a08cbac931354474b0c8f3fb5abbfadd
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
export ROOT_PASSWORD=f360746aba7640928f277b9433a76da4
EOF

    # --- Use Transactional Tables ---
    /bin/cp -f ${source_tree}/donomo_archive/mysqld/my.cnf /etc/my.cnf
    chown root:root /etc/my.cnf
    chmod 644 /etc/my.cnf

    # --- Init Script ---
    /bin/cp -f ${source_tree}/donomo_archive/init.d/donomo-dbinit /etc/init.d/
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
    cat >> /etc/sysconfig/iptables << "EOF"
-A INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 443 -j ACCEPT
EOF

    # --- SE Linux ---
    cat >> /etc/sysconfig/system-config-securitylevel << EOF
--port=80
--port=443
EOF

    # --- Init Script ---
    /bin/cp -f ${source_tree}/donomo_archive/init.d/donomo-app /etc/init.d/
    chown root:root /etc/init.d/donomo-app
    chmod 750 /etc/init.d/donomo-app

    # --- Config Files ---
    /bin/cp -f /home/donomo/nginx/* /etc/nginx/
    chown root:root /etc/nginx/*
    chmod 644 /etc/nginx/*

    # --- SSL Certificate ---
    mkdir -p /etc/ssl/certs
    mkdir -p /etc/ssl/private
    chmod -R 700 /etc/ssl
    cp ${source_tree}/xen/priv/donomo.crt /etc/ssl/certs/
    cp ${source_tree}/xen/priv/donomo.key /etc/ssl/private/
    chmod 600 /etc/ssl/certs/* /etc/ssl/private/*

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
    # note that nginx will be started/stopped by donomo-app as necessary

    chkconfig donomo-app on
fi

if [[ $processors -eq 1 ]]
then
    # --- Init Script ---
    /bin/cp -f ${source_tree}/donomo_archive/init.d/donomo-procs /etc/init.d/
    chown root:root /etc/init.d/donomo-procs
    chmod 750 /etc/init.d/donomo-procs

    # -- Turn on Services ---
    chkconfig donomo-procs on
fi

cat >> /etc/sysconfig/iptables << "EOF"
-A INPUT -j REJECT --reject-with icmp-host-prohibited
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
COMMIT
EOF

chmod 600 /etc/sysconfig/iptables
chmod 644 /etc/sysconfig/system-config-securitylevel

#
# Compile the bits that don't come as packages
#

if [[ $(( python + processors + application )) -gt 0 ]]
then
    rpm -i /tmp/updates/pyPdf-1.12-1.fc10.noarch.rpm

    ( cd /tmp/updates/iulib && scons && scons install )
    ( cd /tmp/updates/tesseract-ocr && ./configure CXXFLAGS="-fPIC -O2" && make && make install )
    ( cd /tmp/updates/ocropus-0.3 && ./configure --without-fst --without-leptonica --without-SDL CXXFLAGS="-fPIC -O2" && make && make install )
fi

#
# Post Boot Script
#

/bin/cp -f ${source_tree}/donomo_archive/init.d/rc.local /etc/rc.d/
chown root:root /etc/rc.d/rc.local
chmod 750 /etc/rc.d/rc.local

#
# Clean up /home/donomo
#

/bin/rm -rf /home/donomo/init.d
/bin/rm -rf /home/donomo/nginx
/bin/rm -rf /home/donomo/mysqld
/bin/rm -rf /home/donomo/solr


#
# Clean the /root directory and your shell history and exit from the image
#
/bin/rm -rf /root/*
chown -R root:root /root/.donomo
chmod 700 /root/.donomo
chmod 600 /root/.donomo/*

/bin/cp -f /home/donomo/.bash* /root/
echo -n '' > /root/.bash_history
chown root:root /root/.bash*
chmod 640 /root/.bash*

cat > /root/.emacs <<EOF
;;disable splash screen and startup message
(setq inhibit-startup-message t)
(setq initial-scratch-message nil)

;;enable syntax highlight by default
(global-font-lock-mode t)
(setq font-lock-maximum-decoration t)

;; enable visual feedback on selections
(setq transient-mark-mode t)
(line-number-mode t)
(column-number-mode t)

;; Force to use spaces for tabs and to be 4 spaces
(setq-default indent-tabs-mode nil)
(setq-default tab-width 4)

;; Set up my C/C++ preferences
(setq c-default-style "bsd")

(defun my-c++-mode-hook ()
  (setq tab-width 4)
  (setq indent-tabs-mode nil)
  (setq c-indent-level 4))

(add-hook 'c++-mode-hook 'my-c++-mode-hook)

(setq auto-mode-alist
      (cons '("\\.\\(c\\|C\\|cpp\\|h\\|H\\|hpp\\)$" . c++-mode)
	    auto-mode-alist))

;; Delete trailing whitspace from files
(add-hook 'write-file-functions 'delete-trailing-whitespace)

;; Use shift-arrows to navigate
(windmove-default-keybindings)
EOF
updatedb
