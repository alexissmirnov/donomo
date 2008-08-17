"""
OCR Process Driver
"""

from donomo.archive            import operations
from donomo.archive.service    import ProcessDriver, indexer
from logging                   import getLogger
import os

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#


MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
logging = getLogger(MODULE_NAME)

# ---------------------------------------------------------------------------

def get_driver():

    """ Factory function to retrieve the driver object implemented by this
        this module
    """

    return OcrDriver()

# ---------------------------------------------------------------------------

class OcrDriver(ProcessDriver):

    """ OCR Process Driver
    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    SERVICE_NAME = MODULE_NAME

    DEFAULT_OUTPUTS = [
        ('ocr_text', [indexer.MODULE_NAME]),
        ]

    ACCEPTED_CONTENT_TYPES = [ 'image/jpeg' ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def handle_work_item(self, item):

        """
        Process a work item.  The work item will be provided and its
        local temp file will be cleaned up by the process driver
        framework.  If this method returns true, the work item will
        also be removed from the work queue.

        """
        local_path = item['Local-Path']
        # ocropus outputs HTML
        output_path = local_path + '.html'

        if 0 != os.system('ocroscript rec-tess %s > %s' % (local_path, output_path)):
            logging.error('Failed to OCR source JPEG: %s' % local_path)
            return False
        
        operations.create_page_view_from_file(
            self.processor,
            OcrDriver.DEFAULT_OUTPUTS[0][0],
            item['Object'].page,
            output_path,
            'text/html' )

        return True
