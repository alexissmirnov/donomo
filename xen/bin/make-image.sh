#!/bin/bash -e

set -x

source ./parse-args.sh

aws_dir=$(cd $(dirname $0)/../aws && pwd)

#if [[ $(( processors + database + application )) -eq 0 ]]
#then
#    echo "At least one image type must be specified"
#    exit 1
#fi

if [[ -e $mount_point ]]
then
    echo "$mount_point already exists!"
    exit 1
fi

if [[ -e $volume_file ]]
then
    echo "$volume_file already exists!"
    exit 1
fi

mkdir -p ${output_dir}

YUM_CONF=${output_dir}/yum.conf
YUM="/usr/bin/yum -c $YUM_CONF --installroot=${mount_point} -y"
YUM_DBG="debuginfo-install --installroot=${mount_point} -y"
CHROOT="chroot ${mount_point}"
UPDATES=${mount_point}/tmp/updates

echo "---- Initializating AMI Filesystem --------------------------------"

echo "Creating volume file (${volume_file}) ..."
dd if=/dev/zero of=${volume_file} bs=1M count=4096

echo "Initializing file system ..."
mke2fs -F -j ${volume_file}

echo "Mounting the filesystem ..."
mkdir -p ${mount_point}
mount -o loop ${volume_file} ${mount_point}

echo "Initializing devices ..."
mkdir ${mount_point}/dev
for i in console null zero;
do
    echo "    Creating device: $i"
    /sbin/MAKEDEV -d ${mount_point}/dev -x $i
done

echo "Initializing directory tree ..."
mkdir -p $UPDATES
mkdir -p ${mount_point}/data
mkdir -p ${mount_point}/etc
mkdir -p ${mount_point}/etc/news
mkdir -p ${mount_point}/proc
mkdir -p ${mount_point}/var
mkdir -p ${mount_point}/var/adm
mkdir -p ${mount_point}/var/arpwatch
mkdir -p ${mount_point}/var/ftp
mkdir -p ${mount_point}/var/gopher
mkdir -p ${mount_point}/var/lib/yum
mkdir -p ${mount_point}/var/log
mkdir -p ${mount_point}/var/spool/uucp
mkdir -p ${mount_point}/var/cache/yum
mkdir -p ${mount_point}/sys/block
touch ${mount_point}/etc/mtab

echo "Creating filesystem tables ..."
cat > ${mount_point}/etc/fstab << EOF
/dev/sda1 / ext3 defaults,noatime 1 1
/dev/sda3 swap swap defaults 0 0
none /dev/pts devpts gid=5,mode=620 0 0
none /dev/shm tmpfs defaults 0 0
none /proc proc defaults 0 0
none /sys sysfs defaults 0 0
/dev/sda2 /data ext3 defaults,noatime 1 2
EOF

echo "Mounting proc filesystem ..."
mount -t proc none ${mount_point}/proc

echo "Configuring yum for Fedora ${fedora_version} ..."

basearch=i386
releasever=${fedora_version}

cat > $YUM_CONF <<EOF
[main]
cachedir=/var/cache/yum
debuglevel=2
distroverpkg=fedora-release
exactarch=1
exclude=*-debuginfo
gpgcheck=0
installonly_limit=2
keepcache=0
logfile=/var/log/yum.log
metadata_expire=1800
obsoletes=1
pkgpolicy=newest
plugins=1
reposdir=/dev/null
tolerant=1

[core]
name=Fedora $releasever - i386
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/releases/$releasever/Everything/$basearch/os/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-$releasever&arch=$basearch
enabled=1

[updates]
name=Fedora $releasever - i386 - updates
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/updates/$releasever/i386/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f$releasever&arch=$basearch
enabled=1

[updates-new-key]
name=Fedora $releasever - i386 - updates (new key)
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/updates/$releasever/$basearch.newkey/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f$releasever.newkey&arch=$basearch
enabled=1

[updates-testing]
name=Fedora $releasever - i386 - Test Updates
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/updates/testing/$releasever/$basearch/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-testing-f$releasever&arch=$basearch
enabled=0

[updates-testing-newkey]
name=Fedora $releasever - i386 - Test Updates - New Key
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/updates/testing/$releasever/$basearch.newkey/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-testing-f$releasever.newkey&arch=$basearch
enabled=0
EOF

#
# Install Base components
#

${YUM} groupinstall Base
${YUM} install yum-utils
#${YUM} install kernel-xen # has drifted out of sync
${YUM} install dstat iptraf
${YUM} install vim-enhanced
${YUM} install emacs
${YUM} install svn
#${YUM_DBG} openssl

wget -N -O "$UPDATES/xen-kernel.tgz" \
    "http://ec2-downloads.s3.amazonaws.com/ec2-modules-2.6.18-xenU-ec2-v1.0-i686.tgz"

tar -C ${mount_point} -xvzf "$UPDATES/xen-kernel.tgz"

#
# Java
#

if [[ $(( ec2 + solr )) -gt 0 ]]
then
    ${YUM} install java
fi

#
# EC2 Tools
#

if [[ $ec2 -eq 1 ]]
then
    ${YUM} install ruby
    wget -N -O "$UPDATES/ec2-ami-tools.noarch.rpm" \
	"http://s3.amazonaws.com/ec2-downloads/ec2-ami-tools.noarch.rpm"
    ${CHROOT} rpm -i "/tmp/updates/ec2-ami-tools.noarch.rpm"

    wget -N -O "$UPDATES/ec2-api-tools.zip" \
	"http://s3.amazonaws.com/ec2-downloads/ec2-api-tools.zip"

    (cd ${mount_point}/usr/local && unzip "$UPDATES/ec2-api-tools.zip")
fi


#
# MySQL Database
#

if [[ $database -eq 1 ]]
then
    ${YUM} groupinstall 'MySQL Database'
fi

#
# Solr
#

if [[ $solr -eq 1 ]]
then
    wget -N -P $UPDATES "http://gulus.usherbrooke.ca/pub/appl/apache/lucene/solr/1.3.0/apache-solr-1.3.0.tgz"
    tar -C $mount_point/usr/local -xvzf $UPDATES/apache-solr-1.3.0.tgz
fi

#
# Python
#

if [[ $(( python + processors + application )) -gt 0 ]]
then
    #
    # Latest Python
    #

    ${YUM} install python
    ${YUM} install python-crypto
    ${YUM} install python-imaging
    ${YUM} install python-reportlab
    ${YUM} install python-BeautifulSoup
    ${YUM} install python-boto
    ${YUM} install python-flup
    ${YUM} install python-httplib2
    ${YUM} install python-simplejson
    ${YUM} --enablerepo=updates-testing --enablerepo=updates-testing-newkey install MySQL-python
    ${YUM} install libtiff
    ${YUM} install ImageMagick
    wget -N -O $UPDATES/pyPdf-1.12-1.fc10.noarch.rpm \
        'http://download.fedora.redhat.com/pub/fedora/linux/development/i386/os/Packages/pyPdf-1.12-1.fc10.noarch.rpm'
    ${CHROOT} rpm -i /tmp/updates/pyPdf-1.12-1.fc10.noarch.rpm
fi

#
# Development Tools and libraries
#

if [[ $development -eq 1 ]]
then
    ${YUM} groupinstall "Development Tools"
    ${YUM} install httpd-devel apr-devel apr-util-devel libapreq2-devel openssl-devel curl-devel expat-devel libetpan-devel createrepo
    ${YUM} install boost-devel ImageMagick-devel ImageMagick-c++-devel
fi

#
# Donomo bits
#

(cd $UPDATES && svn export --non-interactive http://svn2.assembla.com/svn/vaultit/trunk)

#
# Web Server
#

if [[ $application -eq 1 ]]
then
    ${YUM} install nginx
fi

${CHROOT} /tmp/updates/trunk/xen/bin/config-image.sh "$@"
rm -rf $UPDATES

umount ${mount_point}/proc
umount ${mount_point}

source $aws_dir/aws.sh
prefix=donomo-f${fedora_version}-ami-$(date '+%Y%m%d-%H%M')
ec2-bundle-image --arch i386 -i ${volume_file} -c $aws_dir/cert-*.pem -k $aws_dir/pk-*.pem -u $AWS_ACCOUNT_NUMBER -d ${output_dir}  -p $prefix --kernel $aki #--ramdisk $ari
ec2-upload-bundle -b ami.donomo.com -m ${output_dir}/${prefix}.manifest.xml -a $AWS_ACCESS_KEY_ID -s $AWS_SECRET_ACCESS_KEY --retry
#ec2-register ami.donomo.com/${prefix}.manifest.xml
