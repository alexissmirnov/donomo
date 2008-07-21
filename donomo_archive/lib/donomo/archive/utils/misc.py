"""
Miscellaneous stuff.

"""

from django.core.urlresolvers import reverse
import re
import mimetypes

#
# pylint: disable-msg=C0103,W0142
#
#   C0103 - variables at module scope must be all caps
#   W0142 - use of * and ** magic
#

# ---------------------------------------------------------------------------

def guess_mime_type( file_name, default = None ):
    """
    Guess the mime type of the given path or url, falling back to a binary
    blob if we can't decipher the type.

    """
    return ( mimetypes.guess_type(file_name) [0]
             or default
             or 'application/octet-stream' )

# -----------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------

def get_url( viewname, *args, **kwargs ):
    """
    Wrapper for the reverse function.

    """
    return reverse( viewname = viewname, args = args, kwargs = kwargs )

# ---------------------------------------------------------------------------

true_re = re.compile(r'^\s*(true)|(yes)|1\s*$', re.IGNORECASE)

def param_is_true(value):
    """
    Returns true if the value given can be interpreted as affirmative.

    """
    return true_re.match(value.strip()) is not None

# ---------------------------------------------------------------------------

false_re = re.compile(r'^\s*(false)|(no)|0\s*', re.IGNORECASE)

def param_is_false(value):
    """
    Returns true if the value given can be interpreted as negative.

    """
    return false_re.match(value.strip()) is not None

# ---------------------------------------------------------------------------
