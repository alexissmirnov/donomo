"""
Multi-page PDF parser

"""

from donomo.archive                        import operations
from donomo.archive.service                import ocr, DEFAULT_THUMBNAIL_OUTPUTS
from donomo.archive.service.tiff_parser    import TiffParserDriver
from donomo.archive.models                 import Upload
from donomo.archive.utils                  import pdf, image
from logging                               import getLogger
from glob                                  import glob
from PIL                                   import Image
import shutil
import os


#
# pylint: disable-msg=C0103,R0922,W0703
#
#   C0103 - variables at module scope must be all caps
#   R0922 - Abstract class is only referenced once
#   W0703 - Catch "Exception"

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
logging = getLogger(MODULE_NAME)

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

    SERVICE_NAME = MODULE_NAME

    DEFAULT_OUTPUTS = (
        ( 'pdf-original',      []),
        ( 'jpeg-original',      [ocr.MODULE_NAME]) )\
         + DEFAULT_THUMBNAIL_OUTPUTS

    ACCEPTED_CONTENT_TYPES = [ 'application/pdf' ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def process_page_file( self,
                           document,
                           pdf_orig_path,
                           page_number = None ):
        """
        Convert the given PDF file (representing a s single page) to a
        JPEG.
        """
        base_name      = os.path.splitext(pdf_orig_path)[0]
        jpeg_orig_path = pdf.convert(pdf_orig_path, 'jpeg')
        original = Image.open(jpeg_orig_path)
        
        jpeg_t100_path = '%s-thumb-100.jpeg' % base_name
        jpeg_t200_path = '%s-thumb-200.jpeg' % base_name
        image.make_thumbnail(original, 100, jpeg_t100_path)
        image.make_thumbnail(original, 200, jpeg_t200_path)

        page = operations.create_page(document, page_number)
        i = 0
        for path in ( pdf_orig_path, 
                      jpeg_orig_path, 
                      jpeg_t100_path, 
                      jpeg_t200_path) :
            operations.create_page_view_from_file(
                self.processor,
                PdfParserDriver.DEFAULT_OUTPUTS[i][0],
                page,
                path )
            i = i + 1

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
                'Creating new document for %s: %s' % (
                    upload.owner,
                    title))

            document = operations.create_document(
                owner = upload.owner,
                title = title )

            page_number = 0
            pdf_pages = glob(os.path.join(page_dir,'*.pdf'))
            pdf_pages.sort()
            
            for pdf_orig_path in pdf_pages:
                page_number += 1
                self.process_page_file(document, pdf_orig_path, page_number)

            logging.info(
                'done. parsed pdfs for document %s by %s' % (
                    document,
                    document.owner))
        except Exception, e:
            logging.error(e)
            return False
        finally:
            if page_dir:
                shutil.rmtree(page_dir)
                
        return True
# ----------------------------------------------------------------------------
