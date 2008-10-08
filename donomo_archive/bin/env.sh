
export DONOMO_HOME=$(cd $(dirname ${0:?})/.. && pwd)
export PYTHONPATH=$DONOMO_HOME/deps:$DONOMO_HOME/lib${PYTHONPATH:+:$PYTHONPATH}
export DJANGO_SETTINGS_MODULE=donomo.settings

