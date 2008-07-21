"""
Test suite driver
"""

import os
import re
import logging
import unittest

logging = logging.getLogger('test-suite')

# ----------------------------------------------------------------------------

def all_modules_from( root_module ):
    """
    Get a list of all modules starting from the given fully qualivied
    root_module.  The root_module itself is included in the results.
    The root module is expected to be a directory based module.

    """
    search_root  = os.path.dirname(__import__(root_module, {}, {}, ['']).__file__)
    ignored_dirs = [ 'CVS', '.svn', '_svn' ]
    module_list  = []

    # Figure out how much of the path to drop when converting the path
    # to a module hierarchy.
    prefix = search_root
    for i in root_module.split('.'):
        prefix = os.path.dirname(prefix)
    prefix_len = len(prefix) + (prefix.endswith(os.sep) and 0 or 1)
    python_file_re = re.compile(r'^[a-zA-Z_]\w+.py$')

    # Iterate over all directories beneath the search root, adding
    # modules to the module list as they are discovered.
    for crnt_path, dirs, files in os.walk(search_root):

        # Only look at directories representing modules
        if not '__init__.py' in files:
            del dirs[0:]
            continue

        # Don't search ignored directories
        [ dirs.remove(d) for d in dirs if d in ignored_dirs ]

        # Break up the path into fully qualified module components
        module_components = crnt_path[prefix_len:].split(os.sep)

        # Create a list of file based sub-module components.  Each
        # sub-module component is itself a list where the empty list
        # represents the module itself, and each other list has only
        # one element which is the name of the file based sub-module.
        # We ignore __init__.py since we handle the current module
        # it explicitly as the empty list.
        sub_module_components = (
            [ [] ] +
            [ [os.path.splitext(f)[0]]
              for f in files
              if python_file_re.match(f) and f != '__init__.py' ] )

        # output a fully qualified module name for each of the
        # sub-module components
        module_list.extend(
            [ '.'.join(module_components + sub_module_component)
              for sub_module_component in sub_module_components ] )

    # Return the final list
    return module_list

# ----------------------------------------------------------------------------

def suite( root_module = 'donomo.archive' ):
    """
    Return the full test suite
    """
    module_names = all_modules_from(root_module)

    def load_test_suite(module_name):
        try:
            return unittest.defaultTestLoader.loadTestsFromName(module_name)
        except:
            logging.error(
                'Failed to import %s' % module_name)
            return unittest.TestSuite()

    return unittest.TestSuite(
        [ load_test_suite(module_name) for module_name in module_names ])


# ----------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main( defaultTest = 'suite' )
