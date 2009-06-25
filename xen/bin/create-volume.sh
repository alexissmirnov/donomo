volume_file=$1
tmp_dir=/tmp/create-volume
fedora_version=8
architecure=i386

#
# Set-up our commands for later
#

if [[ -n "${volume_file}" ]]
then
    mount_point="${volume_file}.mnt"
    yum_conf="${mount_point}/${tmp_dir}/prep-image-yum.conf"
    yum_opts="-c '${yum_conf}' --install_root='${mount_point}'"
    CHROOT="chroot '${mount_point}'"
else
    mount_point=''
    yum_opts=''
    CHROOT=''
fi

MKDIR="/binmkdir -pv"
YUM="/usr/bin/yum -y ${YUM_OPTS}"
WGET="/usr/bin/wget --directory-prefix=${mount_point}/${tmp_dir}"
CP="/bin/cp -f"
MV="/bin/mv -f"
MOUNT="/bin/mount"
UNMOUNT="/bin/umount -f"

#
# Create temporary directory
#

${MKDIR} ${mount_point}/${tmp_dir}

#
# Set-up disk and install OS if we're using a volume file
#

if [[ -n "${volume_file}" ]]
then
    echo "---- Creating loopback filesystem volume for AMI ----------------------"

    echo "Creating volume file (${volume_file}) ..."
    dd if=/dev/zero of=${volume_file} bs=1M count=3072

    echo "Initializing file system ..."
    mke2fs -F -j ${volume_file}

    echo "Mounting the filesystem ..."
    ${MKDIR} ${mount_point}
    ${MOUNT} -o loop ${volume_file} ${mount_point}

    trap "${UNMOUNT} ${mount_point}/proc; ${UNMOUNT} ${mount_point}; /bin/rmdir ${mount_point}" 0 1 2 15

    echo "Initializing devices ..."
    ${MKDIR} ${mount_point}/dev
    for i in console null zero;
    do
        echo "    Creating device: $i"
        /sbin/MAKEDEV -d ${mount_point}/dev -x $i
    done

    echo "Initializing directory tree ..."
    ${MKDIR} ${mount_point}/data
    ${MKDIR} ${mount_point}/etc
    ${MKDIR} ${mount_point}/etc/news
    ${MKDIR} ${mount_point}/proc
    ${MKDIR} ${mount_point}/var
    ${MKDIR} ${mount_point}/var/adm
    ${MKDIR} ${mount_point}/var/arpwatch
    ${MKDIR} ${mount_point}/var/ftp
    ${MKDIR} ${mount_point}/var/gopher
    ${MKDIR} ${mount_point}/var/lib/yum
    ${MKDIR} ${mount_point}/var/log
    ${MKDIR} ${mount_point}/var/spool/uucp
    ${MKDIR} ${mount_point}/var/cache/yum
    ${MKDIR} ${mount_point}/sys/block
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
name=Fedora ${fedora_version} - i386
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/releases/${fedora_version}/Everything/${architecture}/os/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-${fedora_version}&arch=${architecture}
enabled=1

[updates]
name=Fedora ${fedora_version} - i386 - updates
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/updates/${fedora_version}/i386/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f${fedora_version}&arch=${architecture}
enabled=1

[updates-new-key]
name=Fedora ${fedora_version} - i386 - updates (new key)
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/updates/${fedora_version}/${architecture}.newkey/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f${fedora_version}.newkey&arch=${architecture}
enabled=1

[updates-testing]
name=Fedora ${fedora_version} - i386 - Test Updates
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/updates/testing/${fedora_version}/${architecture}/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-testing-f${fedora_version}&arch=${architecture}
enabled=0

[updates-testing-newkey]
name=Fedora ${fedora_version} - i386 - Test Updates - New Key
#baseurl=http://download.fedora.redhat.com/pub/fedora/linux/updates/testing/${fedora_version}/${architecture}.newkey/
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=updates-testing-f${fedora_version}.newkey&arch=${architecture}
enabled=0
EOF

    ${YUM} groupinstall Base
fi

#
# The packages we know we need
#

${YUM} install yum-utils
${YUM} install vim-enhanced
${YUM} install emacs
${YUM} install svn
${YUM} groupinstall "Development Tools"
${YUM} install httpd-devel apr-devel apr-util-devel libapreq2-devel openssl-devel curl-devel expat-devel libetpan-devel createrepo
${YUM} install boost-devel ImageMagick-devel ImageMagick-c++-devel libpng-devel
${YUM} install scons
${YUM} install ruby
${YUM} groupinstall 'MySQL Database'
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
#${YUM} install kernel-xen # has drifted out of sync
#${YUM_DBG} openssl${YUM} install dstat iptraf


# XEN Kernel for EC2
${WGET} "http://ec2-downloads.s3.amazonaws.com/ec2-modules-2.6.18-xenU-ec2-v1.0-i686.tgz"
${CHROOT} tar -C "/" -xvzf "${tmp_dir}/xen-kernel.tgz"

# EC2 AMI Tools
${WGET} "http://s3.amazonaws.com/ec2-downloads/ec2-ami-tools.noarch.rpm"
${CHROOT} rpm -i "${tmp_dir}/ec2-ami-tools.noarch.rpm"

# EC2 API Tools
${WGET} "http://s3.amazonaws.com/ec2-downloads/ec2-api-tools.zip"
${CHROOT} unzip -d "/usr/local" "${tmp_dir}/ec2-api-tools.zip"

# PyPDF RPM
${WGET} 'http://download.fedora.redhat.com/pub/fedora/linux/releases/10/Everything/i386/os/Packages/pyPdf-1.12-1.fc10.noarch.rpm'
${CHROOT} rpm -i "${tmp_dir}/pyPdf-1.12-1.fc10.noarch.rpm"

# iulib
${WGET} "http://iulib.googlecode.com/files/iulib-0.3.tar.gz"
${CHROOT} tar -C ${tmp_dir} -xvzf ${tmp_dir}/iulib-0.3.tar.gz
${CHROOT} scons -C ${tmp_dir}/iulib
${CHROOT} scons -C ${tmp_dir}/iulib install

# Tessearct OCR
svn export -r 227 --non-interactive "http://tesseract-ocr.googlecode.com/svn/trunk/" ${mount_point}/${tmp_dir}/tesseract-ocr
${CHROOT) bash -c "cd '${tmp_dir}/tesseract-ocr' && ./configure CXXFLAGS='-fPIC -O2'"
${CHROOT} make -C "${tmp_dir}/tesseract-ocr"
${CHROOT} make -C "${tmp_dir}/tesseract-ocr install"

# ocropus
${WGET} "http://ocropus.googlecode.com/files/ocropus-0.3.1.tar.gz"
${CHROOT} tar -C ${tmp_dir} -xvzf ${tmp_dir}/ocropus-0.3.1.tar.gz
${CHROOT) bash -c "cd '${tmp_dir}/ocropus-0.3' && ./configure --without-fst --without-leptonica --without-SDL CXXFLAGS='-fPIC -O2'"
${CHROOT} make -C "${tmp_dir}/ocropus-0.3"
${CHROOT} make -C "${tmp_dir}/ocropus-0.3 install"
