#!/bin/sh

if [[ "$0" = "-bash" ]]
then
    THIS_DIR=$(pwd)
else
    THIS_DIR=$(cd $(dirname $0) && pwd)
fi

EC2_HOME=$(/bin/ls -d /usr/local/ec2-api-tools* 2> /dev/null | sort | tail -1)
EC2_PRIVATE_KEY=$(/bin/ls -d $THIS_DIR/pk-*.pem 2> /dev/null | sort | tail -1)
EC2_CERT=$(/bin/ls -d $THIS_DIR/cert-*.pem 2> /dev/null | sort | tail -1)
JAVA_HOME=$(dirname $(dirname $(dirname $(dirname $(locate libjvm.so | sort | tail -1)))))

if [[ -n "$EC2_HOME" ]] && [[ -n "$EC2_PRIVATE_KEY" ]] && [[ -n "$EC2_CERT" ]]
then
    echo "Adding EC2 information to the environment"
    export EC2_HOME
    export EC2_PRIVATE_KEY
    export EC2_CERT
    export JAVA_HOME
    export PATH=$PATH:$EC2_HOME/bin
else
    echo 2> "EC2 information not added to the environment, are you in the right directory?"
fi
