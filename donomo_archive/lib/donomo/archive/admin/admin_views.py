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
    'queue_list',
    'queue_info',
    'status',
    )

# ----------------------------------------------------------------------------

@staff_member_required
@http_method_dispatcher
def queue_list():
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
def queue_info():
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
def status():
    """
    Dispatch map for HTTP operations on the status page
    """
    return {
        'GET'    : get_status,
        'DELETE' : wipe_everything,
        }

# ----------------------------------------------------------------------------
