from __future__ import with_statement
from django.conf                     import settings
from donomo.archive                  import models

import ConfigParser
import os
import signal

def update_sync_config():
    """ Signal the offlineimap daemon to reload its configuration.
    """
    with open('/var/run/donomo/offlineimap.pid') as pid_file:
        pid = int(pid_file.read())

    os.kill(pid, signal.SIGHUP)

    return True
