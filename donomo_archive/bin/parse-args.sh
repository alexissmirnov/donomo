function show_usage
{
    cat <<EOF
Usage: $1 [-a] [-d] [-p] [-s] [-x] [-e] [-v FILE] [-m PATH]

    -a        install and configure the web applicaton
    -d        install and configure the database
    -p        install and configure the processing pipeline
    -s        install and configure the search index
    -y        install python and tools (implied by -a and -p)
    -x        install development tools
    -e        install ec2 tools and credentials
    -v FILE   create the volume file at the path given by FILE
    -m PATH   mount the volume file (specified with -v) at PATH
EOF
}

while getopts 'adpsxev:m:' flag
do
    case $flag in
        a)
            application=1
            ;;
        d)
            database=1
            ;;
        p)
            processors=1
            ;;
        s)
            solr=1
            ;;
        x)
            development=1
            ;;
        e)
            ec2=1
            ;;
        y)
            python=1
            ;;
        v)
            volume_file=$OPTARG
            ;;
        m)
            mount_point=$OPTARG
            ;;
        *)
            show_usage $(basename $0)
            exit 1
    esac
done

aws_dir=../../aws
fedora_version=8
aki=aki-9b00e5f2
ari=ari-a51cf9cc

echo "------------------------------------------------------------------------"
echo "Volume File : ${volume_file:?}"
echo "Mount Point : ${mount_point:?}"
echo "Processors  : ${processors:=0}"
echo "Database    : ${database:=0}"
echo "Application : ${application:=0}"
echo "SOLR  p     : ${solr:=0}"
echo "Development : ${development:=0}"
echo "EC2 Tools   : ${ec2:=0}"
echo "Fedora      : ${fedora_version}"
echo "------------------------------------------------------------------------"
