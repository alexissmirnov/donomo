#!/bin/sh

exec 2>&1

bin_dir=$(dirname $0)
work_dir=/data/ami

/bin/rm -rf ${work_dir}
/bin/mkdir -p ${work_dir}

${bin_dir}/make-image.sh "$@" -o ${work_dir}

/bin/umount -f ${work_dir}/mnt/proc || /bin/true
/bin/umount -f ${work_dir}/mnt || /bin/true

