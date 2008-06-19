"""
OCR Process Driver
"""

from donomo.archive.service import ProcessDriver
from logging import getLogger

logging = getLogger('OCR')

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

    SERVICE_NAME = 'OCR'

    DEFAULT_OUTPUTS = [
        ('ocr_text', 'text/plain', ['donomo.archive.index']),
        ]

    ACCEPTED_CONTENT_TYPES = [ 'image/tiff' ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def handle_work_item(self, item):

        """ Process a work item.  The work item will be provided and
            its local temp file will be cleaned up by the process driver
            framework.  If this method returns true, the work item will
            also be removed from the work queue.
        """

        local_path = item['Local-path']

        if 0 != run_command('tesseract %r %r' % (local_path, local_path)):
            logging.error('Failed to OCR source TIFF: %s' % local_path)
            return False

        #
        # tesseract adds .txt extension to the output
        #
        local_path += '.txt'

        self.create_page_view_from_file(
            output_channel = 'ocr_text',
            page           = item['Object'].page,
            path           = local_path )

        return True
