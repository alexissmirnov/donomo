""" Donomo Archive urls that are user visible.
"""

from django.conf.urls.defaults import *

urlpatterns = patterns(
    ''
    (r'^admin/', include('donomo.archive.admin_urls')),
    (r'^api/1.0/', include('donomo.archive.api_urls')),
    (r'', include('donomo.archive.user_urls')),
)

