""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults import *
from donomo.archive import user_views

urlpatterns = patterns(
    'docstore.core.views',
    (r'^page/(?P<page_id>\d+)/?$', user_views.page_details, name='page_details'),
    (r'^document/(?P<id>\d+)/$?', user_views.document_details, name='document_details'),
    (r'^document/$?', 'doc_index', user_views.document_list, name='document_list'),
    (r'$', user_views.front_page, 'front_page'),
)

