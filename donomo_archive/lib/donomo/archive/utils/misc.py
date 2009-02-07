"""
Miscellaneous stuff.

"""

from django.core.urlresolvers import reverse
import re
import mimetypes
import BeautifulSoup

#
# pylint: disable-msg=C0103,W0142
#
#   C0103 - variables at module scope must be all caps
#   W0142 - use of * and ** magic
#
###############################################################################

def guess_mime_type( file_name, default = 'application/octet-stream' ):
    """
    Guess the mime type of the given path or url, falling back to a binary
    blob if we can't decipher the type.

    """
    return mimetypes.guess_type(file_name) [0] or default

###############################################################################
def guess_extension(type):
    """
    A utility to fix up the stupid image/jpeg -> jpe extension done by mimetypes
    module
    """
    ext = mimetypes.guess_extension(type)
    if ext == '.jpe':
        return '.jpg'
    else:
        return ext

###############################################################################--

def make_property( func ):
    """
    A decorator function which uses the return value and attributes of
    the given function to create an object instance property.

    func is expected to have a doc string, and to return a dictionary
    containing one or more of the following entries:

        fget -> f(self)           : the getter function
        fset -> g(self, value)    : the setter functon
        fdel -> h(self)           : the delete function

    See:

        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/205183
        http://kbyanc.blogspot.com/2007/06/python-property-attribute-tricks.html

    For example:

        class Example(object):
            @make_property
            def foo():
                'docstring for foo'
                def fget(self):
                    return self._foo
                def fset(self, value):
                    self._foo = value
                return locals()

    """
    return property( doc = func.__doc__, **func() )


###############################################################################

def get_url( viewname, *args, **kwargs ):
    """
    Wrapper for the reverse function.

    """
    # TODO: FIXME -reverse() returns URLs in the forms of //?api/1.0/bla/...

    return reverse( viewname = viewname, args = args, kwargs = kwargs )

###############################################################################

true_re = re.compile(r'^\s*(true)|(yes)|1\s*$', re.IGNORECASE)

def param_is_true(value):
    """
    Returns true if the value given can be interpreted as affirmative.

    """
    return true_re.match(value.strip()) is not None

###############################################################################

false_re = re.compile(r'^\s*(false)|(no)|0\s*', re.IGNORECASE)

def param_is_false(value):
    """
    Returns true if the value given can be interpreted as negative.

    """
    return false_re.match(value.strip()) is not None

###############################################################################

def extract_text_from_html( html ):
    """
    Extracts all plain text from HTML string. Used in indexing.

    """
    # Clean the text from HTML tags
    bsoup = BeautifulSoup.BeautifulSoup(html)

        # Remove all comments
    comments = bsoup.findAll(
        text=lambda text:isinstance(text, BeautifulSoup.Comment))

    for comment in comments:
        comment.extract()

    # Remove all script elements
    for script_element in bsoup.findAll('script'):
        script_element.extract()

    # Now get the text of the body
    body = bsoup.body(text=True)
    text = ''.join(body)

    return text

###############################################################################
def get_hocr_page_dimentions(page_soup):
    """
    Returns width and heigth of an HOCR page. Expects an instance 
    of BeutifulSoup object that represents HOCR file
    """
    ocr_page = page_soup.find('div', {'class' : 'ocr_page'})
    title_parts = ocr_page['title'].split(';')
    
    page_width = -1
    page_height = -1
    for title_part in title_parts:
        bbox = title_part.strip().split(' ')
        
        if bbox[0] == 'bbox':
            page_width = int(bbox[3]) - int(bbox[1])
            page_height = int(bbox[4]) - int(bbox[2])
    
    return page_width, page_height

###############################################################################
def get_hocr_lines(page_soup):
    """
    Returns a list of HOCR lines (x,y, text) from an HOCR page. 
    Expects an instance of BeutifulSoup
    object that represents HOCR file
    """
    lines = list()
    ocr_lines = page_soup.findAll('span', {'class' : 'ocr_line'})
    for ocr_line in ocr_lines:
        if ocr_line.has_key('title'):
            # HOCR title takes the form of title="bbox 755 909 807 936"
            ocr_line_title_parts = ocr_line['title'].split(' ') 
            if ocr_line_title_parts[0] == 'bbox':
                lines.append(
                             {'x' : int(ocr_line_title_parts[1]),
                              'y': int(ocr_line_title_parts[2]),
                              'text': ocr_line.renderContents()})
    return lines

###############################################################################
def extract_text_from_hocr( hocr ):
    """
    Returns image size and a list of text fragments from HOCR string
    """
    bsoup = BeautifulSoup.BeautifulSoup(hocr)

    h, w = get_hocr_page_dimentions(bsoup)
    lines = get_hocr_lines(bsoup)
    return h, w, lines


def days_since(d, now=None):
    """                                                                                                                                     
    Takes two datetime objects and returns the number of days between them.                                                                 
    If d occurs after now, then 0 is returned.                                                                                              
                                                                                                                                            
    Adapted from django.utils.timesince                                                                                                     
    """
    import time
    import datetime
    from django.utils.tzinfo import LocalTimezone

    # Convert datetime.date to datetime.datetime for comparison                                                                             
    if d.__class__ is not datetime.datetime:
        d = datetime.datetime(d.year, d.month, d.day)
    if now:
        t = now.timetuple()
    else:
        t = time.localtime()
    if d.tzinfo:
        tz = LocalTimezone(d)
    else:
        tz = None
    now = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5], tzinfo=tz)

    # ignore microsecond part of 'd' since we removed it from 'now'                                                                         
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    if delta.days <= 0:
        return 0
    