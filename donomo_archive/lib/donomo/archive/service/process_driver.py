#!/usr/bin/env python

""" Driver script which runs the processing pipeline
"""

import time
import threading
import signal
import traceback
import logging
import optparse
import os

MUST_SHUT_DOWN = False
SERVICE_MODULE = 'donomo.archive.service'
MODULE_NAME    = os.path.splitext(os.path.basename(__file__))[0]
logging        = logging.getLogger(MODULE_NAME)

# ---------------------------------------------------------------------------

def stop_process_driver(*args):
    """ Signal handler called when a shutdown must
    """
    logging.info('Shutting down')
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

    def __init__(self, name, options, driver_list):
        """ Construct a new process thread
        """
        threading.Thread.__init__(self, name = name)
        logging.debug('Starting thread %s' % self)
        self.options = options
        self.driver_list = driver_list
        self.setDaemon(True)
        self.start()
        time.sleep(2)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def __str__(self):
        """
        A string representing this thread
        """
        return self.getName()

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def run(self):
        """ Thread main
        """
        while True:
            for driver in self.driver_list:

                if must_shut_down():
                    logging.debug('Stopping thread %s' % self)
                    return

                try:
                    performed_work = driver.run_once()
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

    options, driver_names = parser.parse_args()

    if len(driver_names) == 0:
        driver_names = [
            'pdf_parser',
            'tiff_parser',
            'ocr',
            'indexer',
            ]

    driver_list = [ get_process_driver(name) for name in driver_names ]

    thread_list = [
        ProcessThread( 'Worker-%03d' % i, options, driver_list)
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

