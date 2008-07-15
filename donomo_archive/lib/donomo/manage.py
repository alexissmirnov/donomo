#!/usr/bin/env python
from django.core.management import execute_manager
import os

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

DJANGO_SETTINGS_MODULE = os.environ.get(
    'DJANGO_SETTINGS_MODULE',
    'donomo.settings' )

try:
    settings = get_module(DJANGO_SETTINGS_MODULE)
except ImportError:
    import sys
    sys.stderr.write("Error: Failed to import %s" % DJANGO_SETTINGS_MODULE)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
