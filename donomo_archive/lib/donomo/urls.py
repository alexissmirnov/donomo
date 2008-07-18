""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults import *
from django.conf               import settings

urlpatterns = patterns(
    '',
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
    (r'^/?', include('donomo.archive.urls')),
)
