""" Donomo Archive urls that are user visible.
"""
from django.conf.urls.defaults import patterns, include

urlpatterns = patterns(
    '',
    (r'^admin/', include('donomo.archive.admin.urls')),
    (r'^api/1.0/', include('donomo.archive.api.api_urls')),
    (r'^account/', include('donomo.archive.account.account_urls')),
    (r'', include('donomo.archive.ui.ui_urls')),
)

