#!/usr/bin/env python

""" Driver script which runs the processing pipeline
"""

from donomo.archive import operations
from donomo.archive.service import driver
import time
import threading
import signal
import logging
import optparse
import os
import Queue

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

DEFAULT_PROCESSORS = ( 'pdf_parser', 'tiff_parser', 'ocr', 'indexer', 'pdf_generator' )

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

def load_modules( name_list ):
    """ Create a mapping form service names to the corresponding module
    """
    modules = {}

    for name in name_list:
        module = driver.init_module(name)
        modules[name] = module
        driver.init_processor(module)

    return modules

##############################################################################

def thread_proc( options, work_item ):
    """ Handle a work item (in a thread) by spawning a helper process
    """

    status = -1
    try:
        status = os.system(
            '/usr/bin/env'                                        \
                ' python -m donomo.archive.service.driver.helper' \
                ' %(Process-Name)s %(Asset-ID)s %(Is-New)s' % work_item )
    finally:
        operations.close_work_item( work_item, status == 0 )
        options.queue.put(True)


##############################################################################

def handle_work_item(options, work_item):
    """ Kick off a thread to handle the given work item.
    """
    thread = threading.Thread(
        target = thread_proc,
        args   = ( options, work_item ) )
    thread.start()
    options.max_concurrency -= 1

##############################################################################

def maybe_get_next( options):
    """ If the maximum number of jobs is already active just sleep.
        Otherwise, try to get another job to run.
    """
    if options.max_concurrency < 1:
        time.sleep(2)
        return None

    return operations.retrieve_work_item(
        interrupt_func = must_shut_down,
        auto_get_asset = False)


##############################################################################

def check_for_done( options ):
    """ Check if any jobs finished while we weren't looking.  If so, free
        up concurrency slots.
    """
    try:
        while True:
            options.queue.get(False)
            options.max_concurrency += 1
    except Queue.Empty:
        pass

##############################################################################

def main():

    """ Main.
    """

    signal.signal( signal.SIGTERM, stop_process_driver )
    signal.signal( signal.SIGINT,  stop_process_driver )

    parser = optparse.OptionParser()

    parser.add_option(
        '--max-concurrency',
        default = 3,
        type    = 'int')

    parser.add_option(
        '--daemonize',
        action  = 'store_true',
        default = False )

    parser.add_option('--workdir')
    parser.add_option('--logfile')
    parser.add_option('--umask', type='int')
    parser.add_option('--pidfile')

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
        pidfile = open(options.pidfile, 'w')
        try:
            pidfile.write('%d\n' % os.getpid())
        finally:
            pidfile.close()

    logging.info("Starting")

    if len(process_names) == 0:
        process_names = DEFAULT_PROCESSORS

    options.processes = load_modules(process_names)
    options.queue     = Queue.Queue()

    # pylint: disable-msg=W0702
    #   -> no exception type given
    while not must_shut_down():
        try:

            work_item = maybe_get_next(options)

            if work_item:
                handle_work_item( options, work_item )

            check_for_done(options)

        except:
            logging.exception('An exception occurred!')
    # pylint: enable-msg=W0702

    logging.info("Stopped")


##############################################################################

if __name__ == '__main__':
    main()

