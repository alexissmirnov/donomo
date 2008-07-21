"""
URL to view mappings for admin functions.

"""

#
# pylint: disable-msg=W0401
#
#   W0401 - wildcard import
#

from django.conf.urls.defaults import url, patterns
from donomo.archive.admin.admin_views import *

urlpatterns = patterns(
    '',
    url( r'^uploads/$', uploads, name='admin_uploads' ),
    url( r'^queues/(?P<queue_name>\w+)/$', queue_info, name = 'admin_queue_info' ),
    url( r'^queues/?$', queue_list, name = 'admin_queue_list' ),
    url( r'^/?$', status, name='admin_status' ),
)

