"""
AJAX API Views.

"""

#
# pylint: disable-msg=W0401
#
#   W0401 - wildcard import
#

from django.contrib.auth.decorators  import login_required
from donomo.archive.utils.http       import http_method_dispatcher
from donomo.archive.api.api_impl     import *

__all__ = (
    'document_list',
    'document_info',
    'document_view',
    'page_info',
    'page_view',
    'tag_list',
    'tag_info',
    )

# ---------------------------------------------------------------------------

@login_required
@http_method_dispatcher
def document_list():
    """
    Dispatch map for HTTP opoerations on the document list.

    """
    update_map = {
        'upload' : upload_document,
        'split'  : split_document,
        'merge'  : merge_documents,
    }

    def apply_update_map(request):
        """
        Dispatch map for update operations on a document.

        """
        return update_map[request['op'].strip().lower()](request)

    return {
        'GET'   : get_document_list,
        'POST'  : apply_update_map

        }

# ---------------------------------------------------------------------------

@login_required
@http_method_dispatcher
def document_info():
    """
    Dispatch map for HTTP operations on a document

    """
    return {
        'GET'    : get_document_info,
        'PUT'    : update_document,
        'DELETE' : delete_document,
        }

# ---------------------------------------------------------------------------

@login_required
@http_method_dispatcher
def document_view():
    """
    Dispatch map for HTTP operations on a document view

    """
    return {
        'GET' : get_document_view,
        }

# ----------------------------------------------------------------------------

@login_required
@http_method_dispatcher
def page_info():
    """
    Dispatch map for HTTP operations on a page

    """
    return {
        'GET'    : get_page_info,
        'DELETE' : delete_page,
        }

# ----------------------------------------------------------------------------

@login_required
@http_method_dispatcher
def page_view():
    """
    Dispatch map for HTTP operations on a page view

    """
    return {
        'GET' : get_page_view,
        }

# ----------------------------------------------------------------------------

@login_required
@http_method_dispatcher
def tag_list():
    """
    Dispatch map for HTTP operations on the tag list

    """
    return {
        'GET'  : get_tag_list,
        'POST' : create_tag,
        }

# ----------------------------------------------------------------------------

@login_required
@http_method_dispatcher
def tag_info():
    """
    Dispatch map for HTTP operations on a tag

    """
    return {
        'GET'    : get_tag_info,
        'DELETE' : delete_tag,
        'PUT'    : tag_documents,
        }

# ----------------------------------------------------------------------------

