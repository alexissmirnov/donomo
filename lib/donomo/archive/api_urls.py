""" Donomo Archive urls that form the AJAX API
"""

from django.conf.urls.defaults import *
from donomo.archive import api_views

urlpatterns = patterns(
    '',
    (r'^documents/$?', api_views.document_list, name='api_document_list'),
    (r'^documents/(?P<id>\d+)/$?', api_views.document_info, name='api_document_info'),
    (r'^pages/(?P<id>\d+)/?$', api_views.page_info, name='api_page_info'),
    (r'^tags/?$', api_views.page_info, name='api_tag_list'),
)

