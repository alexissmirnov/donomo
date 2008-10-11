#!/bin/sh

THIS_DIR=${DONOMO_AWS:=$(cd $(dirname $0) && pwd)}

EC2_HOME=$(ls -d /usr/local/ec2-api-tools* 2> /dev/null | sort | tail -1)
EC2_PRIVATE_KEY=$(ls -d $THIS_DIR/pk-*.pem 2> /dev/null | sort | tail -1)
EC2_CERT=$(ls -d $THIS_DIR/cert-*.pem 2> /dev/null | sort | tail -1)

if [[ -n "$EC2_HOME" ]] && [[ -n "$EC2_PRIVATE_KEY" ]] && [[ -n "$EC2_CERT" ]]
then
    export EC2_HOME
    export EC2_PRIVATE_KEY
    export EC2_CERT
    export PATH=$PATH:$EC2_HOME/bin
fi
