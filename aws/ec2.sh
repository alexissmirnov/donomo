export AWS_ACCESS_KEY_ID=13Q9QPDKZE5BBGJHK7R2
export AWS_SECRET_ACCESS_KEY=om9OUC3onE699qGCw2Z70xay0hnqFssLq+jwMCXx
export AWS_ACCOUNT_NUMBER=111647622032

THIS_DIR=$(cd $(dirname $0) && pwd)
EC2_HOME=$(ls -d /usr/local/ec2-api-tools* 2> /dev/null | sort | tail -1)
EC2_PRIVATE_KEY=$(ls -d $THIS_DIR/pk-*.pem 2> /dev/null | sort | tail -1)
EC2_CERT=$(ls -d $THIS_DIR/cert-*.pem 2> /dev/null | sort | tail -1)

if [[ -n "$EC2_HOME" -a -n "EC2_PRIVATE_KEY" -a -n "EC2_CERT" ]]
then
    export EC2_HOME
    export EC2_PRIVATE_KEY
    export EC2_CERT
    export PATH=$EC2_HOME/bin:$PATH
fi