#!/usr/bin/env python

""" Driver script which runs offline imap in a loop to keep pulling mails.
"""

from __future__ import with_statement

from logging import getLogger

import time
import signal
import logging
import optparse
import os
import subprocess

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

logging = getLogger('offlineimapd')

MUST_SHUT_DOWN = False
MUST_RESTART = False

# ----------------------------------------------------------------------------

def on_stop_signal(*args):
    """ Signal handler called when a shutdown must
    """

    # pylint: disable-msg=W0603,W0613
    #   W0603 - use of global keyword
    #   W0613 - unused argument
    logging.info('Received termination signal')
    global MUST_SHUT_DOWN
    MUST_SHUT_DOWN = True
    # pylint: enable-msg=W0603,W0613

# ----------------------------------------------------------------------------

def on_restart_signal(*args):
    # pylint: disable-msg=W0603,W0613
    #   W0603 - use of global keyword
    #   W0613 - unused argument
    logging.info('Received reload signal')
    global MUST_RESTART
    MUST_RESTART=True
    # pylint: enable-msg=W0603,W0613

# ----------------------------------------------------------------------------

def must_shut_down():
    """ Check if the offlineimap daemon supposed to shut down
    """
    return MUST_SHUT_DOWN

def must_restart():
    """ Check if the offlineimap daemon supposed to restart
    """
    return MUST_RESTART


def terminate(child):
    global MUST_RESTART
    MUST_RESTART = False
    while child.poll() is None:
        logging.info('Sending shutdown signal to offlineimap worker')
        os.kill(child.pid, signal.SIGTERM)
        time.sleep(1)

# ----------------------------------------------------------------------------

def main():
    """ Main.
    """

    signal.signal( signal.SIGTERM, on_stop_signal )
    signal.signal( signal.SIGINT,  on_stop_signal )
    signal.signal( signal.SIGHUP,  on_restart_signal )

    parser = optparse.OptionParser()

    parser.add_option(
        '--daemonize',
        action  = 'store_true',
        default = False )

    parser.add_option('--workdir')
    parser.add_option('--logfile')
    parser.add_option('--umask', type='int')
    parser.add_option('--pidfile')
    parser.add_option('--frequency', type='int')
    parser.add_option(
        '--config',
        dest='config_file',
        default='/vol/offlineimap/offlineimap.conf')
    parser.add_option(
        '--quiet',
        dest = 'verbosity',
        action = 'store_const',
        const = 'Quiet',
        default = 'Basic' )

    options, _extras = parser.parse_args()

    if options.daemonize:
        from django.utils.daemonize import become_daemon
        daemon_kwargs = {}
        if options.workdir:
            daemon_kwargs['our_home_dir'] = options.workdir
        if options.logfile:
            daemon_kwargs['out_log'] = options.logfile
            daemon_kwargs['err_log'] = options.logfile
        if options.umask:
            daemon_kwargs['umask'] = options.umask
        become_daemon( **daemon_kwargs)

    if options.pidfile:
        with open(options.pidfile, 'wb') as pidfile:
            pidfile.write('%d\n' % os.getpid())

    options.config_file = os.path.abspath(options.config_file)

    logging.info('Starting offlineimapd')

    while not must_shut_down():
        try:
            os.system(
                "'%s' '%s'" % (
                    os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__),
                            'gen-offlineimap-conf')),
                    options.config_file ))

            params = [
                'offlineimap', # will show up as the process name
                '-c', "from offlineimap import init; init.startup(\'6.2.0\')",
                '-c', options.config_file,
                ]


            child = subprocess.Popen(params, executable='/usr/bin/python')

            while not ( must_shut_down() or must_restart() ):
                if child.poll() is not None:
                    break
                time.sleep(1)

            terminate(child)

        except Exception:
            logging.exception('An exception occurred!')

    if options.pidfile:
        os.remove(options.pidfile)

    logging.info("Stopped")


##############################################################################

if __name__ == '__main__':
    main()

