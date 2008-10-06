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
from donomo.archive.utils.basic_auth import logged_in_or_basicauth
__all__ = (
    'document_list',
    'document_info',
    'document_as_pdf',
    'page_info',
    'page_view',
    'page_as_pdf',
    'tag_list',
    'tag_info',
    'search'
    )

###############################################################################
@logged_in_or_basicauth()
@login_required
@http_method_dispatcher
def document_list():
    """
    Dispatch map for HTTP operations on the document list.

    """
    update_map = {
        'upload' : upload_document,
        'split'  : split_document,
        'merge'  : merge_documents, # default
    }

    def apply_update_map(request):
        """
        Dispatch map for update operations on a document.

        """
        return update_map[request.GET.get('op', 'upload').strip().lower()](request)

    return {
        'GET'   : get_document_list,
        'POST'  : apply_update_map
        }

###############################################################################

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

###############################################################################

@login_required
@http_method_dispatcher
def document_as_pdf():
    """
    Get PDF of a document
    """
    return {
        'GET' : get_document_pdf,
        }

###############################################################################

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

###############################################################################

@login_required
@http_method_dispatcher
def page_view():
    """
    Dispatch map for HTTP operations on a page view

    """
    return {
        'GET' : get_page_view,
        }

###############################################################################

@login_required
@http_method_dispatcher
def page_as_pdf():
    """
    Get PDF of a document
    """
    return {
        'GET' : get_page_pdf,
        }

###############################################################################

@login_required
@http_method_dispatcher
def tag_list():
    """
    Dispatch map for HTTP operations on the tag list

    """
    return {
        'GET'  : get_tag_list,
        }

###############################################################################

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

###############################################################################

@login_required
@http_method_dispatcher
def search():
    """
    Dispatch map for HTTP operations on search

    """
    return {
        'GET'  : get_search,
        }

###############################################################################



