#!/usr/bin/env python

""" Driver script which runs the processing pipeline
"""

import time
import threading
import signal
import traceback
import logging as logging_module
import optparse

MUST_SHUT_DOWN = False
SERVICE_MODULE = 'donomo.archive.service'

logging = logging_module.getLogger('process_driver')

# ---------------------------------------------------------------------------

def stop_process_driver(*args):
    """ Signal handler called when a shutdown must
    """
    global MUST_SHUT_DOWN
    MUST_SHUT_DOWN = True

# ---------------------------------------------------------------------------

def must_shut_down():
    """ Check if the process driver is supposed to shut down
    """
    return MUST_SHUT_DOWN

# ---------------------------------------------------------------------------

class ProcessThread(threading.Thread):

    """ Active object which runs through the processing pipeline
    """

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def __init__(self, name, options, process_list):
        """ Construct a new process thread
        """
        threading.Thread.__init__(self, name = name)
        self.options = options
        self.process_list = process_list
        self.setDaemon(True)
        self.start()
        time.sleep(2)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def run(self):
        """ Thread main
        """
        while True:
            for process in self.process_list:

                if must_shut_down():
                    return

                try:
                    performed_work = process.run_once()
                except:
                    logging.error(traceback.print_exc())
                    performed_work = False

                time.sleep(
                    performed_work and 1 or self.options.sleep_period)


# ---------------------------------------------------------------------------

def get_process_driver( name ):

    """ Get a process driver instance
    """

    return __import__(
        '%s.%s' % (SERVICE_MODULE, name),
        {},
        {},
        [''] ).get_driver()

# ---------------------------------------------------------------------------

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
        '--sleep-period',
        default = 5,
        type    = 'int' )

    options, process_names = parser.parse_args()

    if len(process_names) == 0:
        process_names = [
            'tiff_parser',
            'ocr',
            'indexer',
            ]

    process_list = [ get_process_driver(name) for name in process_names ]

    thread_list = [
        ProcessThread( 'Worker-%03d' % i, process_list) \
            for i in xrange(1, 1 + options.num_threads)
        ]

    for thread in thread_list:
        while True:
            thread.join(0.5)
            if not thread.isAlive():
                break

    print "Stopped"


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    main()

