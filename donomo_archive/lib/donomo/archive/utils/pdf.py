from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from PIL import Image
from cStringIO import StringIO

# ---------------------------------------------------------------------------

def _draw_page_list(page_list, buffer = None, view_type = None):
    """ Draw a list of pages into a pdf file
    """

    # todo figure out page size based on the pdi and x/y ratio

    if buffer is None:
        buffer = StringIO()

    if view_type is None:
        view_type = 'jpeg-original'

    canvas = Canvas(buffer)

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

    return buffer

# ---------------------------------------------------------------------------

def render_document(document,  buffer = None, view_type = None):

    """ Renders a document as a PDF file
    """

    return _draw_page_list(
        [ b.page for b in document.bindings.order_by('page_number') ],
        buffer,
        view_type )

# ---------------------------------------------------------------------------

def render_page(page, buffer = None, view_type = None):

    """ Renders a page as a PDF file
    """

    return _draw_page_list(
        [ page ],
        buffer,
        view_type )
