
# -----------------------------------------------------------------------------

def make_property( func ):
    """ A decorator function which uses the return value and attributes of
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

