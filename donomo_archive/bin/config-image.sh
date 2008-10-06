#!/bin/sh -e

set -x

source $(dirname $0)/parse-args.sh "$@"

#
# Check consistency of passwd and group files and make appropriate corrections
#

pwck -r
grpck -r

# Convert passwd and group files to shadow (/etc/shadow and /etc/gshadow
# respectively)
#
pwconv
grpconv

# Set default root password on instance;
#
passwd root

cat <<EOF > /etc/sysconfig/network
NETWORKING=yes
HOSTNAME=localhost.localdomain
EOF

cat <<EOF > /etc/sysconfig/network-scripts/ifcfg-eth0
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
sed -i 's/^#?PermitRootLogin\s+\w+/PermitRootLogin without-password/' /etc/ssh/sshd_config
sed -i 's/^#?PasswordAuthentication\s+\w+/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#?UseDNS\s+\w+/UseDNS no/' /etc/ssh/sshd_config
sed -i 's/^#?ClientAliveInterval\s+\d+/ClientAliveInterval 60/' /etc/ssh/sshd_config
sed -i 's/^#?ClientAliveCountMax\s+\d+/ClientAliveCountMax 240/' /etc/ssh/sshd_config

# Create and populate /root/.ssh directory
#
mkdir -p /root/.ssh
if [[ -f /tmp/updates/authorized_keys ]]
then
    cp /tmp/updates/authorized_keys /root/.ssh/
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
#
#
EOF

cat >> /etc/init.d/rc.local <<'EOF'
#!/bin/bash

touch /var/lock/subsys/local


#
# Fetch public key using HTTP (if one was supplied at launch)
#

curl -f http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key > /tmp/my-key
if [ $? -eq 0 ] ;
then
    cat /tmp/my-key >> /root/.ssh/authorized_keys
    rm -f /tmp/my-key
    sort -u /root/.ssh/authorized_keys > /root/.ssh/new_authorized_keys
    mv /root/.ssh/new_authorized_keys /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
fi

#
# Grab instance parameters
#

EC2_PARAM_URL=http://169.254.169.254/latest
META_DATA_URL=$EC2_PARAM_URL/meta-data
USER_DATA_URL=$EC2_PARAM_URL/user-data
EC2_INFO_DIR=/etc/ec2info
SUMMARY=${EC2INFO}/summary.txt

rm -fr $EC2_INFO_DIR
mkdir -p $EC2_INFO_DIR
touch $SUMMARY

#
# Download instance meta data
#

echo -e \
    "--- Instance Meta-Data -----------------------------------------\n" \
    >> $SUMMARY

for i in $(curl "$META_DATA_URL"); do
    curl "$META_DATA_URL/$i"> ${EC2_INFO_DIR}/$i;
    echo "  $i : $(cat ${EC2_INFO_DIR}/$i)" >> $SUMMARY;
done

#
# Download instance user data
#

echo -e \
    "\n--- Instance Parameters -----------------------------------------\n" \
    >> $SUMMARY

USER_DATA_TEMP=/tmp/user-data
mkdir -p $USER_DATA_TEMP
curl -f $INFOURL/user-data > $USER_DATA_TEMP/user-data.tgz
if [[ $? -ne 0 ]]
then
    echo " * None * "
else
    tar -C $USER_DATA_TEMP -xvzf $USER_DATA_TEMP/userdata.tgz
    rm $USER_DATA_TEMP/userdata.tgz

    for i in $(ls -1 $USER_DATA_TEMP)
    do
        if [[ "$i" =~ "private|secret|password" ]]; then continue; fi

        echo "  $i : $(cat ${USER_DATA_TEMP}/$i)" >> $SUMMARY
        cp ${USER_DATA_TEMP}/$i ${EC2_INFO_DIR}/
    done

    echo "" >> $SUMMARY
fi
rm -rf $USER_DATA_TEMP
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

#set -e

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
# Set up iptables
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

if [[ $application -eq 1 ]]
then
    cat >> /etc/sysconfig/iptables << EOF
-A INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 443 -j ACCEPT
EOF
fi

if [[ $solr -eq 1 ]]
then
    cat >> /etc/sysconfig/iptables << EOF
-A INPUT -m state --state NEW -m tcp -p tcp --dport 8983 -j ACCEPT
EOF
fi

cat >> /etc/sysconfig/iptables << EOF
-A INPUT -j REJECT --reject-with icmp-host-prohibited
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
COMMIT
EOF

chmod 600 /etc/sysconfig/iptables

#
# Set up securitylevel
#

cat > /etc/sysconfig/system-config-securitylevel << EOF
# Configuration file for system-config-securitylevel
--enabled
--port=22:tcp
EOF

if [[ $application -eq 1 ]]
then
    cat >> /etc/sysconfig/system-config-securitylevel << EOF
--port=80
--port=443
EOF
fi

if [[ $solr -eq 1 ]]
then
    cat >> /etc/sysconfig/system-config-securitylevel << EOF
--port=8983
EOF
fi

chmod 644 /etc/sysconfig/system-config-securitylevel

if [[ $(( application + processors )) -gt 0 ]]
then
    useradd donomo

    mv /tmp/updates/donomo_archive/* /home/donomo/
    mv /tmp/updates/aws.sh /home/donomo/.awsrc
    chown -R donomo:donomo /home/donomo
    chown -R donomo:donomo /home/donomo/.*
    find /home/donomo -type d -print0 | xargs -0 chmod 750
    find /home/donomo -type f -print0 | xargs -0 chmod 640
    chmod 750 /home/donomo/bin/*
fi

if [[ $application -eq 1 ]]
then
    cat > /etc/init.d/donomo-app <<"EOF"
#!/bin/sh -e

workdir=/home/donomo
pidfile=$workdir/logs/application.pid
logfile=$workdir/logs/application.log

function start
{
    if [-e $pidfile ]
    then
        echo >2 "Donomo Processing Pipeline is already running (pid=$(cat $pidfile))"
        exit 1
    fi

    export PYTHONPATH=$workdir/deps:$workdir/lib:$PYTHONPATH
    su donomo -c "$workdir/bin/application runfcgi protocol=fcgi method=prefok daemonize=true pidfild=$pidfile host=127.0.0.1 port=8081 workdir=$workdir out_log=$logfile err_log=$logfile"
}

function stop
{
    if [ -e $pidfile ]
    then
        kill $(cat pidfile)
        rm $pidfile
    fi
}

case ${1:?} in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
    *)
        echo >2 "I don't know how to $1"
        exit 1
esac
EOF
    chmod 700 /etc/init.d/donomo-app
    ln -sf /etc/init.d/donomo-procs /etc/rc.d/rc3.d/S98domono-app
fi

if [[ $processors -eq 1 ]]
then
    cat > /etc/init.d/donomo-procs <<"EOF"
#!/bin/sh -e

workdir=/home/donomo
pidfile=$workdir/logs/processors.pid
logfile=$workdir/logs/processors.log

function start
{
    if [-e $pidfile ]
    then
        echo >2 "Donomo Processing Pipeline is already running (pid=$(cat $pidfile))"
        exit 1
    fi

    export PYTHONPATH=$workdir/deps:$workdir/lib:$PYTHONPATH
    su donomo -c "$workdir/bin/processors --daemonize --pidfild=$pidfile --workdir=$workdir --logfile=$logfile"
}

function stop
{
    if [ -e $pidfile ]
    then
        kill $(cat pidfile)
        rm $pidfile
    fi
}

case ${1:?} in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
    *)
        echo >2 "I don't know how to $1"
        exit 1
esac
EOF
    chmod 700 /etc/init.d/donomo-procs
    ln -sf /etc/init.d/donomo-procs /etc/rc.d/rc3.d/S98domono-procs
fi



#
# Clean the /root directory and your shell history and exit from the image
#
rm -rf /root/*
echo -n '' > /root/.bash_history
