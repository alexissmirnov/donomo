""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults     import patterns, url
from django.views.generic.simple   import direct_to_template
from donomo.archive.api.api_views  import document_view, page_view
from donomo.archive.ui.ui_views    import front_page

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

urlpatterns = patterns(
    '',
    url(
        regex  = r'^page/(?P<id>\d+)/?$',
        view   = page_view,
        name   = 'ui_page_view'),

    url(
        regex  = r'^document/(?P<id>\d+)/?$',
        view   = document_view,
        name   = 'ui_document_view'),

    url(
        regex  = r'^archive/?$',
        view   = direct_to_template,
        kwargs = { 'template' : 'ui/archive.html' },
        name   = 'ui_archive' ),

    url(
        regex  = r'^archive2/?$',
        view   = direct_to_template,
        kwargs = { 'template' : 'ui/archive-module-panel.html' },
        name   = 'ui_archive2' ),

    url(
        regex  = r'^$',
        view   = front_page,
        name   = 'ui_front_page'),
    )

