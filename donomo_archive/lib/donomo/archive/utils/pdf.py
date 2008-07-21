"""
Utilities for dealing with PDF files and in-memory streams
"""

from reportlab.pdfgen.canvas    import Canvas
from reportlab.lib.units        import inch
from reportlab.lib.utils        import ImageReader
from PIL                        import Image
from cStringIO                  import StringIO
from shutil                     import rmtree
from tempfile                   import mkdtemp
import os
import logging

logging = logging.getLogger('pdf-utils')

# ---------------------------------------------------------------------------

def _draw_page_list(page_list, output_buffer = None, view_type = None):
    """
    Draw a list of pages into a pdf file

    """
    # todo figure out page size based on the pdi and x/y ratio

    if output_buffer is None:
        output_buffer = StringIO()

    if view_type is None:
        view_type = 'jpeg-original'

    canvas = Canvas(output_buffer)

    for page in page_list:
        image = ImageReader(
            Image.open(
                StringIO(page.download_to_memory(view_type) ['Content'] )))

        canvas.drawImage(
            image,
            0,
            0,
            8.5 * inch,
            11 * inch)
        canvas.showPage()

    canvas.save()

    return output_buffer

# ----------------------------------------------------------------------------

def render_document(document, output_buffer = None, view_type = None):

    """
    Renders a document as a PDF file

    """
    return _draw_page_list(
        document.pages.order_by('position').all(),
        output_buffer,
        view_type )

# ----------------------------------------------------------------------------

def render_page(page, output_buffer = None, view_type = None):
    """
    Renders a page as a PDF file

    """
    return _draw_page_list(
        [ page ],
        output_buffer,
        view_type )

# ----------------------------------------------------------------------------

def split_pages(input_filename):

    """
    Splits up a PDF file into single page PDF files.  Returns
    path string where resulting PDF files are
    located. It is the caller's responsibility to clean the disk when
    the files are no longer necessary. The best way to do it is to
    call result.rmtree()

    This method assumes pdftk is installed.
    See http://www.accesspdf.com/pdftk/ for more info

    """
    output_dir = None
    try:
        # create a temporary directory
        output_dir = mkdtemp('donomo')
        # run pdftk
        os.system('cd %r && pdftk %r burst' % (output_dir, input_filename))
        # return the directory name to the caller
        return output_dir
    except:
        logging.exception('Failed to split PDF')
        # delete a temporary directory along with all its contents
        if output_dir:
            rmtree(output_dir)
        raise

# ----------------------------------------------------------------------------

def convert(input_path, format = 'png', density = 200, quality = 80):
    """
    Converts a PDF file into a file of a given format.  Returns the
    filename of the resulting file

    """
    output_path = '%s.%s' % (
        os.path.splitext(input_path)[0],
        format )

    if 0 != os.system(
        'convert -density %d -quality %d %r %r' % (
            density,
            quality,
            input_path,
            output_path )):
        raise Exception(
            'Failed to convert %r to %s' % (
                input_path,
                output_path))

    return output_path


# ----------------------------------------------------------------------------


