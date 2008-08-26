#!/usr/bin/env python

import os
import sys
import django.core.management

DJANGO_SETTINGS_MODULE = os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'donomo.settings' )

##############################################################################

def get_module(module_name):
    """
    Import a module by name, returning the module.

    """
    module = __import__(module_name)

    for component in module_name.split('.')[1:]:
        module = getattr(module, component)

    return module

##############################################################################

def main():
    """
    Main management program.

    """
    try:
        if sys.argv[1] == 'test':
            os.environ['USE_TEST_SETTINGS'] = 'yes'

        settings = get_module(DJANGO_SETTINGS_MODULE)
    except ImportError:
        sys.stderr.write("Error: Failed to import %s" % DJANGO_SETTINGS_MODULE)
        sys.exit(1)

    django.core.management.execute_manager(settings)

##############################################################################

if __name__ == "__main__":
    main()
