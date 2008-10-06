#!/usr/bin/env python

""" Driver script which runs the processing pipeline
"""

from donomo.archive import operations
from django.db import transaction

import time
import threading
import signal
import traceback
import logging
import optparse
import os

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

DEFAULT_PROCESSORS = ( 'pdf_parser', 'tiff_parser', 'ocr', 'indexer' )

MUST_SHUT_DOWN = False

logging = logging.getLogger('process-driver')

##############################################################################

def stop_process_driver(*args):
    """ Signal handler called when a shutdown must
    """

    # pylint: disable-msg=W0603,W0613
    #   W0603 - use of global keyword
    #   W0613 - unused argument
    logging.info('Shutting down')
    global MUST_SHUT_DOWN
    MUST_SHUT_DOWN = True
    # pylint: enable-msg=W0603,W0613

##############################################################################

def must_shut_down():
    """ Check if the process driver is supposed to shut down
    """
    return MUST_SHUT_DOWN

##############################################################################

def init_processor(module):

    """ Private initialization function to get the processor object
        representing this service.

    """

    return operations.initialize_processor(
        module.__name__.rsplit('.', 1)[-1],
        module.DEFAULT_INPUTS,
        module.DEFAULT_OUTPUTS,
        module.DEFAULT_ACCEPTED_MIME_TYPES ) [0]

##############################################################################

def init_module( name ):
    """ Load and initialize a service module """
    module = __import__('donomo.archive.service.%s' % name, {}, {}, [''])
    init_processor(module)
    return module


##############################################################################

def load_modules( name_list ):
    """ Create a mapping form service names to the corresponding module """
    return dict((name, init_module(name)) for name in name_list)

##############################################################################

@transaction.commit_on_success
def handle_work_item( options, work_item ):
    """ Transactionally handle work item """
    module = options.process[ work_item['Process-Name'] ]
    try:
        success = False
        module.handle_work_item( init_processor(module), work_item )
        success = True
    finally:
        operations.close_work_item( work_item, success)

##############################################################################

def thread_proc( options ):
    """ Thread main """
    # pylint: disable-msg=W0702
    #   -> no exception type given
    while not must_shut_down():
        try:
            work_item = operations.retrieve_work_item(
                interrupt_func = must_shut_down)

            if not work_item:
                continue

            handle_work_item( options, work_item )

        except:
            logging.exception('An exception occurred!')
    # pylint: enable-msg=W0702

##############################################################################

def main():

    """ Main.
    """

    signal.signal( signal.SIGTERM, stop_process_driver )
    signal.signal( signal.SIGINT,  stop_process_driver )

    parser = optparse.OptionParser()

    parser.add_option(
        '--num-threads',
        default = 1,
        type    = 'int')

    parser.add_option(
        '--daemonize',
        action  = 'set_true',
        default = False )

    parser.add_option('--work-dir')
    parser.add_option('--stdout')
    parser.add_option('--stderr')
    parser.add_option('--umask', type='int')
    parser.add_option('--pidfile')

    options, process_names = parser.parse_args()

    if options.daemonize:
        from django.utils.daemonize import become_daemon
        daemon_kwargs = {}
        if options.work_dir:
            daemon_kwargs['out_home_dir'] = options.work_dir
        if options.stdout:
            daemon_kwargs['out_log'] = options.stdout
        if options.stderr:
            daemon_kwargs['err_log'] = options.stderr
        if options.umask:
            daemon_kwargs['umask'] = options.umask
        become_daemon( **daemon_kwargs)

    if options.pidfile:
        pidfile = open(options.pidfile, 'w')
        try:
            pidfile.write('%d\n' % os.getpid())
        finally:
            pidfile.close()

    if len(process_names) == 0:
        process_names = DEFAULT_PROCESSORS

    options.process = load_modules(process_names)

    thread_list = [
        threading.Thread(
            target = thread_proc,
            name   = 'Worker-%03d' % i,
            args   = (options,))
        for i in xrange(1, 1 + options.num_threads)
        ]

    for thread in thread_list:
        thread.setDaemon(True)
        thread.start()

    for thread in thread_list:
        while True:
            thread.join(0.5)
            if not thread.isAlive():
                break

    print "Stopped"


##############################################################################

if __name__ == '__main__':
    main()

