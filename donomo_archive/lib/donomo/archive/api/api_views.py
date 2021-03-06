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
from donomo.archive.utils.middleware import api_login_required

__all__ = (
    'document_list',
    'document_info',
    'document_zip',
    'document_as_pdf',
    'page_info',
    'page_view',
    'page_as_pdf',
    'tag_list',
    'tag_info',
    'search',
    'aggregate_list',
    'aggregate_info',
    'message_info',
    'message_list',
    'sync_event_list',
    'contact_list',
    'contact_info',
    'account_info',
    )

###############################################################################
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

@api_login_required
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

@api_login_required
@http_method_dispatcher
def document_zip():
    """
    Get ZIP of a selection of documents
    """
    return {
        'GET' : get_document_zip,
        }


###############################################################################

@api_login_required
@http_method_dispatcher
def document_as_pdf():
    """
    Get PDF of a document
    """
    return {
        'GET' : get_document_pdf,
        }

###############################################################################

@api_login_required
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

@api_login_required
@http_method_dispatcher
def page_view():
    """
    Dispatch map for HTTP operations on a page view

    """
    return {
        'GET' : get_page_view,
        }

###############################################################################

@api_login_required
@http_method_dispatcher
def page_as_pdf():
    """
    Get PDF of a document
    """
    return {
        'GET' : get_page_pdf,
        }

###############################################################################

@api_login_required
@http_method_dispatcher
def tag_list():
    """
    Dispatch map for HTTP operations on the tag list

    """
    return {
        'GET'  : get_tag_list,
        }

###############################################################################

@api_login_required
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

@api_login_required
@http_method_dispatcher
def search():
    """
    Dispatch map for HTTP operations on search

    """
    return {
        'GET'  : get_search,
        }

###############################################################################

@api_login_required
@http_method_dispatcher
def sync_event_list():
    """
    Dispatch map for HTTP operations on search

    """
    return {
        'GET'  : get_sync_event_list,
        }

###############################################################################

@api_login_required
@http_method_dispatcher
def aggregate_list():
    """
    """
    return {
    'GET' : get_aggregate_list,
    }

###############################################################################

@api_login_required
@http_method_dispatcher
def aggregate_info():
    """
    Dispatch map for HTTP operations on a tag

    """
    return {
        'GET'    : get_aggregate_info,
        }

###############################################################################

@api_login_required
@http_method_dispatcher
def message_info():
    """
    Dispatch map for HTTP operations on a message

    """
    return {
        'GET'    : get_message_info,
        'PUT'    : update_message_info,
        }

###############################################################################
@api_login_required
@http_method_dispatcher
def message_list():
    """
    Dispatch map for HTTP operations on messages

    """
    return {
        'GET'    : get_message_list,
        }
###############################################################################

@api_login_required
@http_method_dispatcher
def contact_list():
    """
    """
    return {
    'GET' : get_contact_list,
    }
###############################################################################

@api_login_required
@http_method_dispatcher
def contact_info():
    """
    """
    return {
    'PUT' : update_contact_info,
    }

###############################################################################

@http_method_dispatcher
def account_info():
    """
    """
    return {
    'PUT' : update_or_create_account,
    }
