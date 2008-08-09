"""
Donomo Archive urls that form the AJAX API

"""

#
# pylint: disable-msg=C0103,W0401
#
#   C0103 - variables at module scope must be all caps
#   W0401 - wildcard import
#

from django.conf.urls.defaults     import patterns, url
from donomo.archive.api.api_views  import *

__all__ = ( 'urlpatterns' )

urlpatterns = patterns(
    '',
    url( r'^documents/$',
         document_list,
         name = 'api_document_list' ),

    url( r'^documents/(?P<pk>\d+)/$',
         document_info,
         name = 'api_document_info' ),

    url( r'^documents/(?P<pk>\d+)/(?P<view_name>[-a-zA-Z0-9_]+)/$',
         document_view,
         name = 'api_document_view' ),

    url( r'^pages/(?P<pk>\d+)/$',
         page_info,
         name = 'api_page_info' ),

    url( r'^pages/(?P<pk>\d+)/(?P<view_name>[-a-zA-Z0-9_]+)/$',
         page_view,
         name = 'api_page_view' ),

    url( r'^tags/$',
         tag_list,
         name = 'api_tag_list' ),

    url( r'^tags/(?P<label>[-a-zA-Z0-9_]+)/$',
         tag_info,
         name = 'api_tag_info' ),
    )

