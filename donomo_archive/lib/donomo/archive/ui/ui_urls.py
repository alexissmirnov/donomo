""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults     import patterns, url
from django.views.generic.simple   import direct_to_template
from donomo.archive.ui.ui_views    import front_page

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

urlpatterns = patterns(
    '',
    url(
        regex  = r'^archive/?$',
        view   = direct_to_template,
        kwargs = { 'template' : 'ui/archive.html' },
        name   = 'ui_archive' ),

    url(
        regex  = r'^$',
        view   = front_page,
        name   = 'ui_front_page'),
    )

