from django.conf.urls.defaults                  import patterns, url
from django.conf.urls.defaults                  import *

urlpatterns = patterns('',
                       url(r'^expense/$', 'donomo.billing.views.expense'),
                )
                        
