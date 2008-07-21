"""
Admin view function entry points

"""

#
# pylint: disable-msg=W0401
#
#   W0401 - wildcard import
#

from django.contrib.admin.views.decorators import staff_member_required
from donomo.archive.utils.http             import http_method_dispatcher
from donomo.archive.admin.admin_impl       import *

__all__ = (
    'uploads',
    'queue_list',
    'queue_info',
    'status',
    )

# ----------------------------------------------------------------------------

@staff_member_required
def uploads(request):
    """
    What is this supposed to be?
    """
    # TODO: what is this supposed to do?
    return HttpResponse('admin wants this for some reason...')


# ----------------------------------------------------------------------------

@staff_member_required
@http_method_dispatcher
def queue_list(request):
    """
    Dispatch map for HTTP operations on the queue list
    """
    return {
        'GET'    : get_queue_list,
        'DELETE' : delete_all_queues,
        }

# ----------------------------------------------------------------------------

@staff_member_required
@http_method_dispatcher
def queue_info(request, queue_name):
    """
    Dispatch map for HTTP operations on the queue list
    """
    return {
        'GET'    : get_queue_info,
        'DELETE' : delete_queue,
        }

# ----------------------------------------------------------------------------

@staff_member_required
@http_method_dispatcher
def status(request):
    """
    Dispatch map for HTTP operations on the status page
    """
    return {
        'GET'    : get_status,
        'DELETE' : wipe_everything,
        }

# ----------------------------------------------------------------------------
