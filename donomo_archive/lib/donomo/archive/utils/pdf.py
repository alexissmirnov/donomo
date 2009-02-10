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
from pyPdf                      import PdfFileWriter, PdfFileReader
import os
import logging
from donomo.archive.utils       import s3, misc
from donomo.archive.models      import AssetClass
from donomo.archive.operations  import instantiate_asset
import urllib

logging = logging.getLogger('pdf-utils')

DPI = 200

##############################################################################

def _draw_page_list(page_list,
                    output_buffer = None,
                    username = None,
                    title = None,
                    view_type = None):
    """
    Draw a list of pages into a pdf file.

    """

    if output_buffer is None:
        output_buffer = StringIO()

    canvas = Canvas(output_buffer)

    if username is not None:
        canvas.setAuthor(username)

    if title is not None:
        canvas.setTitle(title)

    if view_type is None:
        view_type = AssetClass.PAGE_IMAGE

    view_asset_class = AssetClass.objects.get(name = view_type)
    text_asset_class = AssetClass.objects.get(name = AssetClass.PAGE_TEXT)

    for page in page_list:
        # For each page, get S3 URL for an image and HTML representation
        # extract text from the HTML
        # put image and text into PDF canvas
        # NB Image.open seems to only work with a file (not a stream)
        # so we have to create (and delete) a temporary file that
        # holds the image and the text
        image_stream = StringIO()
        image_asset = page.get_asset(view_asset_class)
        image_file = instantiate_asset(image_asset)['Local-Path']
        image = Image.open(image_file)

        text_asset = page.get_asset(text_asset_class)
        text_file = instantiate_asset(text_asset)['Local-Path']

        text = open(text_file,'r').read()
        image_width, image_heigth, text_fragments = misc.extract_text_from_hocr(text)

        w = (image_width/DPI)*inch
        h = (image_heigth/DPI)*inch

        rw = w/image_width
        rh = h/image_heigth

        for fragment in text_fragments:
            canvas.drawString(rw * fragment['x'], h - rh *fragment['y'], fragment['text'])
        canvas.drawInlineImage( image, 0, 0, w, h)
        canvas.setPageSize((w,h))
        canvas.showPage()

        os.remove(image_file)
        os.remove(text_file)

    canvas.save()

    return output_buffer

##############################################################################

def render_document(document,
                    output_buffer = None,
                    username = None,
                    title = None,
                    view_type = None):

    """
    Renders a document as a PDF file

    """
    return _draw_page_list(
        document.pages.order_by('position').all(),
        output_buffer,
        username,
        title,
        view_type )

##############################################################################

def render_page(page,
                output_buffer = None,
                username = None,
                title = None,
                view_type = None):
    """
    Renders a page as a PDF file

    """
    return _draw_page_list(
        [ page ],
        output_buffer,
        username,
        title,
        view_type )

##############################################################################

def split_pages(input_filename, prefix = None):

    """
    Splits up a PDF file into single page PDF files.  Returns
    path string where resulting PDF files are
    located. It is the caller's responsibility to clean the disk when
    the files are no longer necessary. The best way to do it is to
    call result.rmtree()
    """
    output_dir = None
    try:
        if prefix is None:
            # create a temporary directory
            output_dir = mkdtemp('donomo')
            prefix = os.path.join(output_dir, 'page-')

        # open PDF
        pdf_input = PdfFileReader(file(input_filename, 'rb'))

        # iterate over pages in the input PDF
        for i in xrange(pdf_input.getNumPages()):
            # get n-th page
            page = pdf_input.getPage(i)

            # create a one-page pdf writer
            pdf_output = PdfFileWriter()
            pdf_output.addPage(page)

            # save it in a new file
            page_filename = '%s%03d.pdf' % (prefix, i)
            page_filestream = file(page_filename, "wb")
            pdf_output.write(page_filestream)
            page_filestream.close()

        # return the directory name to the caller
        return os.path.dirname(prefix)
    except Exception, e:
        logging.error(str(e))
        # delete a temporary directory along with all its contents
        if output_dir:
            rmtree(output_dir)
        raise

##############################################################################

def convert(
    input_path,
    format = 'jpeg',
    density = DPI,
    quality = 95,
    output_path = None ):

    """
    Converts a PDF file into a file of a given format.  Returns the
    filename of the resulting file

    """
    if output_path is None:
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


