""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults import patterns, include

urlpatterns = patterns(
    '',
#    (r'^admin/', include('donomo.archive.admin.urls')),
    (r'^api/1.0/', include('donomo.archive.api.urls')),
    (r'', include('donomo.archive.ui.urls')),
)

