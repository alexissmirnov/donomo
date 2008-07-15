"""
API for dealing with PDF files and in-memory streams

"""

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from PIL import Image
from cStringIO import StringIO

from docstore.utils.path import path
from tempfile import mkdtemp
from os import system

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

def split(input_filename):

    """
    Splits up a PDF file into single page PDF files.  Returns the
    docstore.utils.path object where resulting PDF files are
    located. It is the caller's responsibility to clean the disk when
    the files are no longer necessary. The best way to do it is to
    call result.rmtree()

    This method assumes pdftk is installed.
    See http://www.accesspdf.com/pdftk/ for more info

    """
    output_dir = path()
    try:
        # create a temporary directory
        output_dir = path(mkdtemp('donomo'))
        # run pdftk
        system('cd %s; pdftk %s burst' % (output_dir, input_filename))
        # return the directory name to the caller
        return output_dir
    except Exception:
        # delete a temporary directory along with all its contents
        output_dir.rmtree()
        raise

# ----------------------------------------------------------------------------

def convert(input_filename, format = 'png', density = 200, quality = 80):

    """
    Converts a PDF file into a file of a given format.  Returns the
    filename of the resulting file
    """

    input_path = path(input_filename)
    input_dir = input_path.parent
    output_filename = input_path.namebase + '.' + format
    system('cd %s; convert -density %d -quality %d %s %s' %
           (input_dir,
            density,
            quality,
            input_filename,
            output_filename))
    return input_dir.joinpath(output_filename)


# ----------------------------------------------------------------------------

import unittest
class TestPdf(unittest.TestCase):
    """
    Unit test for this module

    """
    def test_split_pages(self):
        """
        Split pages

        """
        output_dir = split('/tmp/2008_06_26_15_42_45.pdf')
        map(lambda x: convert(x), output_dir.listdir('*.pdf'))

        print output_dir.listdir()
        output_dir.rmtree()


# ----------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()

