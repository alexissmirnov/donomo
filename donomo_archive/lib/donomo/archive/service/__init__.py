"""
Process driver framework for services exposed in the document processing
pipeline.

"""

from donomo.archive import operations
import logging as logging_module
import os

#
# pylint: disable-msg=C0103,W0142,W0702,R0921
#
#   C0103 - variables at module scope must be all caps
#   W0142 - use of * and ** magic
#   W0702 - catch exceptions of unspecifed type
#   R0921 - unreferenced abstract class
#

__all__ = ( 'ProcessDriver' )
logging = logging_module.getLogger('process_driver')

# ---------------------------------------------------------------------------

class ProcessDriver:

    """ Base class for process driver instances
    """

    SERVICE_NAME = None
    DEFAULT_OUTPUTS = None
    ACCEPTED_CONTENT_TYPES = ()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self):

        """
        Constructor

        """

        self._processor = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @property
    def processor(self):

        """
        The processor represented by this process driver.

        """

        if self._processor is None:
            assert self.SERVICE_NAME, 'ProcessDriver instances require a name'
            self._processor = operations.get_or_create_processor(
                self.SERVICE_NAME,
                self.DEFAULT_OUTPUTS or []  )
        return self._processor

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def handles_content_type( self, content_type ):

        """
        Returns True if the passed content type is in the list of
        types handled by this service.

        """

        return ( content_type in self.ACCEPTED_CONTENT_TYPES )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __str__(self):

        """
        A textual representation of this process driver

        """

        return str(self.processor)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


    def handle_work_item(self, item):

        """
        Derived classes must implement this method to handle a work
        item, returning True if the work item has been successfully
        and completely handled.  The return value will be used to
        determine whether or not the work item should be removed from
        the intput queue for this process.

        """

        raise NotImplementedError()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def system(self, command):
        """
        Run a command, logging the results.

        """
        logging.debug( '%s - %s' % (self, command))
        return os.system(command)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def run_once(self):

        """
        Run one iteration of the process loop

        """

        work_item = operations.get_work_item(self.processor)

        if work_item is None:
            return False

        if not self.handles_content_type( work_item['Content-Type'] ):
            logging.warn(
                '%(Processor)s - dropping item of ' \
                    'unsupported content type: %(Content-Type)s)' \
                    % work_item )
            return True

        was_successful = False
        try:
            try:
                was_successful = self.handle_work_item(work_item)
            except:
                logging.exception('Failed to handle work item')
        finally:
            operations.close_work_item(
                self.processor,
                work_item,
                was_successful)

        return was_successful

# ----------------------------------------------------------------------------
