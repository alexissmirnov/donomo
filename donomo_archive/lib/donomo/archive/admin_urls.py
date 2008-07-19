"""
"""
from django.conf.urls.defaults import patterns, url
from donomo.archive import admin_views

urlpatterns = patterns(
    '',
    url( r'^indexer/$', admin_views.indexer_status, name='admin_indexer_status' ),
    url( r'^queues/(?P<queue_name>\w+)/$', admin_views.queue_status, name = 'admin_queue_status' ),
    url( r'^queues/?$', admin_views.queue_list, name = 'admin_queue_list' ),
    url( r'^/?$', admin_views.summary, name='admin_summary' ),
)

