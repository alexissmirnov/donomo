"""
Multi-page PDF parser

"""

from donomo.archive                        import operations
from donomo.archive.service.tiff_parser    import TiffParserDriver
from donomo.archive.models                 import Upload
from donomo.archive.utils                  import pdf
from logging                               import getLogger
from glob                                  import glob

import shutil
import os


#
# pylint: disable-msg=C0103,R0922
#
#   C0103 - variables at module scope must be all caps
#   R0922 - Abstract class is only referenced once
#

logging = getLogger('PDF Parser')

# ---------------------------------------------------------------------------

def get_driver():
    """
    Factory function to retrieve the driver object implemented by this
    this module

    """
    return PdfParserDriver()

# ---------------------------------------------------------------------------

class PdfParserDriver(TiffParserDriver):

    """
    PDF Parser Process Driver

    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    SERVICE_NAME = 'pdf-parser'

    DEFAULT_OUTPUTS = (( 'pdf-original', []),) \
        + TiffParserDriver.DEFAULT_OUTPUTS

    ACCEPTED_CONTENT_TYPES = [ 'application/pdf' ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def process_page_file( self,
                           document,
                           pdf_orig_path,
                           page_number = None ):
        """
        Convert the given PDF file (representing a s single page) to a
        JPEG (via TIFF).  We punt by doing the conversion to TIFF then
        calling the process_page_file function on the TIFF Parser
        driver (passing this object as fake tiff parser driver
        instance.

        """

        tiff_orig_path = pdf.convert(pdf_orig_path, 'tiff')
        page = TiffParserDriver.process_page_file(
            self,
            document,
            tiff_orig_path,
            page_number)

        operations.create_page_view_from_file(
            self.processor,
            'pdf-original',
            page,
            pdf_orig_path )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def handle_work_item(self, item):
        """
        Pick up a (possibly) multipage PDF upload and turn it into a document
        having (possibly) multiple individual pages.

        """
        local_path = item['Local-Path']
        upload     = item['Object']

        if not isinstance(upload, Upload):
            logging.error('%s - Dropped!  Work item is not an upload!' % self)
            return True

        page_dir = None

        try:
            page_dir = pdf.split_pages(local_path)

            logging.debug('Extracted pages to %s' % page_dir)

            title = 'Uploaded on %s (%s)' % (
                upload.timestamp,
                upload.gateway )

            logging.info(
                '%s - Creating new document for %s: %r' % (
                    upload.owner,
                    title))

            document = operations.create_document(
                owner = upload.owner,
                title = title )

            page_number = 0
            for pdf_orig_path in glob(os.path.join(page_dir,'*.pdf')).sort():
                page_number += 1
                self.process_page_file(document, pdf_orig_path, page_number)

            logging.info(
                'done. parsed pdfs for document %s by %s' % (
                    document,
                    document.owner))
        finally:
            if page_dir:
                shutil.rmtree(page_dir)

# ----------------------------------------------------------------------------
