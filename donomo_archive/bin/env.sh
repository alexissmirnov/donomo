
export PYTHONPATH=${DONOMO_HOME:?}/deps:$DONOMO_HOME/lib${PYTHONPATH:+:$PYTHONPATH}
export DJANGO_SETTINGS_MODULE=donomo.settings

META_DATA=/var/spool/ec2/meta-data.sh
USER_DATA=/var/spool/ec2/user-data.sh

[[ -f $META_DATA ]] && source $META_DATA
[[ -f $USER_DATA ]] && source $USER_DATA

