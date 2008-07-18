""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults import patterns, url
from donomo.archive.user_views import *

urlpatterns = patterns(
    'docstore.core.views',
    (r'^page/(?P<page_id>\d+)/?$', 'user_views.page_info', {'name' : 'page_info'}),
    (r'^document/(?P<id>\d+)/$?', 'user_views.document_info', {'name': 'document_info'}),
    (r'^document/$?', 'doc_index', 'user_views.document_list', {'name':'document_list'}),
    (r'^archive/?$', 'django.views.generic.simple.direct_to_template', {'template' : 'ui/archive.html'} ),
    (r'^archive2/?$', 'django.views.generic.simple.direct_to_template', {'template' : 'ui/archive-module-panel.html'} ),
    (r'$', user_views.front_page, 'front_page'),
)

