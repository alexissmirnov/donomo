""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults import *
from django.conf               import settings
from django.contrib            import admin

admin.autodiscover() #e nable the admin and load each admin.py file:


#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

urlpatterns = patterns(
    '',
    # sproutcore requires /static prefix for its application
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'show_indexes': True, 'document_root' : settings.MEDIA_ROOT + '/static/'}),
    #(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : settings.MEDIA_ROOT + '/sc/build/static/'}),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'show_indexes': True, 'document_root': settings.MEDIA_ROOT }),
    (r'^admin/(.*)', admin.site.root),
    (r'^', include('donomo.archive.urls')),
)
