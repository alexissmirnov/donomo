#!/usr/bin/env python
from django.core.management import execute_manager
import os

DJANGO_SETTINGS_MODULE = os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'donomo.settings' )

# ---------------------------------------------------------------------------

def get_module(module_name):
    """
    Import a module by name, returning the module.

    """
    module = __import__(module_name)

    for component in module_name.split('.')[1:]:
        module = getattr(module, component)

    return module

# ---------------------------------------------------------------------------

def main():
    """
    Main management program.

    """
    try:
        settings = get_module(DJANGO_SETTINGS_MODULE)
    except ImportError:
        import sys
        sys.stderr.write("Error: Failed to import %s" % DJANGO_SETTINGS_MODULE)
        sys.exit(1)

    execute_manager(settings)

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
