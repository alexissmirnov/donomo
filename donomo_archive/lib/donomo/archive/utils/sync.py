from __future__ import with_statement
from django.conf                     import settings
from donomo.archive                  import models

import ConfigParser
import os
import signal
import logging

logging = logging.getLogger('sync')


def update_sync_config():
    """ Signal the offlineimap daemon to reload its configuration.
    """
    with open(settings.OFFLINEIMAP_PID_FILE) as pid_file:
        pid = int(pid_file.read())

    try:
        os.kill(pid, signal.SIGHUP)
    except OSError,e:
        logging.warning(e)
        pass
    
    return True
