"""
Multi-page TIFF parser

"""

from donomo.archive            import operations
from donomo.archive.service    import ProcessDriver
from donomo.archive.models     import Upload
from logging                   import getLogger
from glob                      import glob
from PIL                       import Image

import shutil
import os


#
# pylint: disable-msg=C0103,R0922
#
#   C0103 - variables at module scope must be all caps
#   R0922 - Abstract class is only referenced once
#

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
logging     = getLogger(MODULE_NAME)

# ---------------------------------------------------------------------------

def get_driver():
    """
    Factory function to retrieve the driver object implemented by this
    this module

    """
    return TiffParserDriver()

# ---------------------------------------------------------------------------

class TiffParserDriver(ProcessDriver):

    """
    TIFF Parser Process Driver

    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    SERVICE_NAME = MODULE_NAME

    DEFAULT_OUTPUTS = (
        ( 'tiff-original',      ['donomo.archive.service.ocr']),
        ( 'jpeg-original',      []),
        ( 'jpeg-thumbnail-100', []),
        ( 'jpeg-thumbnail-200', []),
    )

    ACCEPTED_CONTENT_TYPES = [ 'image/tiff' ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def make_thumbnail( self,
                        original,
                        max_edge_length,
                        save_as = None,
                        format = 'JPEG'):
        """
        Create a thumbnail of the given original images, where the
        longest edge has max_edge_length, and the other edge is scaled
        accordingly.  If you specify a file name to save as, the resulting
        thumbnail will be written to disk.

        """
        logging.debug(
            '%s - Creating thumbnail %s, save_as = %s' % (
                self,
                max_edge_length,
                save_as ))

        width, height = original.size

        if width > height:
            ratio = float( height ) / float( width )
            scale = ( max_edge_length,
                      int( ratio * max_edge_length) )
        else:
            ratio = float( width ) / float( height )
            scale = ( int( ratio * max_edge_length),
                      max_edge_length )

        new_image = original.copy()
        new_image.thumbnail(scale, Image.ANTIALIAS)

        if save_as:
            new_image.save(save_as, format)

        return new_image


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def process_page_file( self,
                           document,
                           tiff_orig_path,
                           page_number = None ):
        """
        Convert the given TIFF file (representing a s single page) whose path
        is given to a JPEG (via RGBA).  Also create two thumbnails.

        """

        # Paths we'll need later
        base_name      = os.path.splitext(tiff_orig_path)[0]
        rgba_orig_path = '%s.rgba' % base_name
        jpeg_orig_path = '%s.jpeg' % base_name
        jpeg_t100_path = '%s-thumb-100.jpeg' % base_name
        jpeg_t200_path = '%s-thumb-200.jpeg' % base_name

        # Convert original TIFF to RGBA
        self.system(
            'tiff2rgba %r %r' % (
                tiff_orig_path,
                rgba_orig_path))

        # Save RGBA to JPEG
        original = Image.open(rgba_orig_path)
        original.save(jpeg_orig_path, 'JPEG')

        # Make thunbnails
        self.make_thumbnail(original, 100, jpeg_t100_path)
        self.make_thumbnail(original, 200, jpeg_t200_path)

        # Create the page and upload all the views
        page = operations.create_page(document, page_number)
        for path, view in ( ( tiff_orig_path, 'tiff-original'),
                            ( jpeg_orig_path, 'jpeg-original'),
                            ( jpeg_t100_path, 'jpeg-thumbnail-100'),
                            ( jpeg_t200_path, 'jpeg_thumbnail-200') ) :
            operations.create_page_view_from_file(
                self.processor,
                view,
                page,
                path )

        return page

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def handle_work_item(self, item):
        """
        Pick up a (possibly) multipage TIFF upload and turn it into a document
        having (possibly) multiple individual pages.

        """
        local_path = item['Local-Path']
        upload     = item['Object']

        if not isinstance(upload, Upload):
            logging.error('%s - Dropped!  Work item is not an upload!' % self)
            return True

        page_dir = '%s.pages' % local_path
        os.mkdir(page_dir)

        try:

            logging.debug('Extracting pages to %s' % page_dir)

            self.system(
                'tiffsplit %r %r' % (
                    local_path,
                    os.path.join(page_dir, 'page-')))

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
            for tiff_orig_path in glob(os.path.join(page_dir,'*.tif')).sort():
                page_number += 1
                self.process_page_file(document, tiff_orig_path, page_number)

            logging.info(
                'done. parsed tiffs for document %s by %s' % (
                    document,
                    document.owner))
        finally:
            shutil.rmtree(page_dir)

# ----------------------------------------------------------------------------
