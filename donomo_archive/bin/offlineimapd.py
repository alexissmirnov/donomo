#!/usr/bin/env python

""" Driver script which runs offline imap in a loop to keep pulling mails.
"""

from __future__ import with_statement

from donomo.archive.models import *
from django.conf import settings
from logging import getLogger

import ConfigParser
import time
import signal
import logging
import optparse
import os
import tempfile

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
    logging.info('Shutting down')
    global MUST_SHUT_DOWN
    MUST_SHUT_DOWN = True
    # pylint: enable-msg=W0603,W0613

# ----------------------------------------------------------------------------

def on_restart_signal(*args):
    # pylint: disable-msg=W0603,W0613
    #   W0603 - use of global keyword
    #   W0613 - unused argument
    logging.info('Restarting offlineimap')
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
    while child.poll is None:
        os.kill(child.pid, signal.SIGINT)
        time.sleep(1)

# ----------------------------------------------------------------------------

def generate_conf_file( out_stream ):
    config = ConfigParser.RawConfigParser()

    all_account_names = []
    for account in Account.objects.all():
        account_name = '%s.%s' % (account.owner.username, account.name)
        section_name = 'Account %s' % account_name
        all_account_names.append(account_name)

        config.add_section(section_name)
        config.set(section_name, 'localrepository', '%s.local' % account_name)
        config.set(section_name, 'remoterepository', '%s.remote' % account_name)
        config.set(section_name, 'username', account.owner.username)
        config.set(section_name, 'maxconnections', '3')

        section_name = 'Repository %s.local' % account_name
        config.add_section(section_name)
        config.set(section_name, 'type', 'Maildir')
        config.set(section_name, 'localfolders', '%s/%s' % (settings.OFFLINEIMAP_DATA_DIR, account_name))

        section_name = 'Repository %s.remote' % account_name
        config.add_section(section_name)
        config.set(section_name, 'type', 'Gmail')
        config.set(section_name, 'remoteuser', account.name)
        config.set(section_name, 'remotepass', account.password)

    section_name = general
    config.add_section(section_name)
    config.set(section_name, 'maxsyncaccounts', '50')
    config.set(section_name, 'accounts', ','.join(all_account_names))
    config.set(section_name, 'metadata', '%s/metadata' % settings.OFFLINEIMAP_DATA_DIR)

    config.write(out_stream)
    out_stream.flush()

# ----------------------------------------------------------------------------

def get_config_file( name ):
    """ If a specific named file file is to be used, open it and return
        it; othewise, open and return a named temporary file.
    """
    return name and open(name, 'wb') or tempfile.NamedTemporaryFile()

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
    parser.add_option('--config')
    parser.add_option(
        '--quiet',
        dest = 'verbosity',
        action = store_const,
        const = 'Quiet',
        default = 'Basic' )

    options, process_names = parser.parse_args()

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

    while not must_shut_down():
        with get_config_file(options.config_file) as config_file:
            try:
                generate_config_file(config_file)
                params = [
                    'offlineimap', # will show up as the process name
                    '-c', "from offlineimap import init; init.startup(\'6.2.0\')",
                    '-c', config_file.name,
                    '-u', 'Noninteractive.%s' % options.verbosity,
                    '-l', options.logfile,
                    '-o',
                    ]

                logging.info('Starting offlineimapd')
                child = subprocess.Popen(params, executable='/usr/bin/python')

                while not must_shut_down() and not must_restart():
                    if child.poll() is not None:
                        break
                    time.sleep(5)

                terminate(child)

            except Exception:
                logging.exception('An exception occurred!')

    if options.pidfile:
        os.path.remove(options.pidfile)

    logging.info("Stopped")


##############################################################################

if __name__ == '__main__':
    main()

