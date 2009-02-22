""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults     import patterns, url
from django.views.generic.simple   import direct_to_template
from donomo.archive.ui.ui_views    import front_page, download_tags

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

urlpatterns = patterns(
    '',
    url(
        regex  = r'^view/pages/(?P<id>\d+)/$',
        view   = direct_to_template,
        kwargs = { 'template' : 'ui/page.html' },
        name   = 'ui_view_page' ),

    url(
        regex  = r'^view/download/$',
        view   = download_tags,
        name   = 'ui_download_tags' ),

    url(
        regex  = r'^view/search/$',
        view   = direct_to_template,
        kwargs = { 'template' : 'ui/search.html' },
        name   = 'ui_view_search' ),

    url(
        regex  = r'^$',
        view   = front_page,
        name   = 'ui_front_page'),
    )

