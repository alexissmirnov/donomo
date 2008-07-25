""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults import patterns
from django.conf               import settings

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

urlpatterns = patterns(
    '',
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
    (r'^/?', include('donomo.archive.urls')),
)
