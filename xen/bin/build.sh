#!/bin/sh

bin_dir=$(dirname $0)
work_dir=${1:?}
shift

/bin/rm -rf ${work_dir}
/bin/mkdir -p ${work_dir}

${bin_dir}/make-image.sh "$@" -o ${work_dir}

/bin/umount -f ${work_dir}/mnt/proc || /bin/true
/bin/umount -f ${work_dir}/mnt || /bin/true