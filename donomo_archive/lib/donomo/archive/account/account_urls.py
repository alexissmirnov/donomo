from django.conf.urls.defaults                  import patterns, url

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib.auth import views as auth_views

from registration.views import activate
from donomo.archive.account.account_views import *


urlpatterns = patterns('',
                       # Activation keys get matched by \w+ instead of the more specific
                       # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
                       # that way it can return a sensible "invalid key" message instead of a
                       # confusing 404.
                       url(r'^activate/(?P<activation_key>\w+)/$',
                           activate,
                           {'template_name': 'registration/registration_complete.html'},
                           name='registration_activate'),
                       url(r'^login/$',
                           auth_views.login,
                           name='auth_login'),
                       url(r'^logout/$',
                           auth_views.logout,
                           {'template_name': 'registration/logout.html'},
                           name='auth_logout'),
                       url(r'^password/change/$',
                           auth_views.password_change,
                           name='auth_password_change'),
                       url(r'^password/change/done/$',
                           auth_views.password_change_done,
                           name='auth_password_change_done'),
                       url(r'^password/reset/$',
                           auth_views.password_reset,
                           name='auth_password_reset'),
                       url(r'^password/reset/done/$',
                           auth_views.password_reset_done,
                           name='auth_password_reset_done'),
                       url(r'^register/$',
                           register,
                           name='registration_register'),
                       url(r'^register/complete/$',
                           direct_to_template,
                           {'template': 'registration/activate.html'},
                           name='registration_complete'),
                       url(r'^trial/$',
                           trial,
                           name='trial'),

                       url(r'^(?P<username>[-+@.a-zA-Z0-9_]+)/delete/$', 
                            'donomo.archive.account.account_views.account_delete',
                            name='account-delete'),                                                        
                       url(r'^(?P<username>[-+@.a-zA-Z0-9_]+)/export/$',  
                            'donomo.archive.account.account_views.account_export',
                            name='account-export'),
                       url(r'^(?P<username>[-+@.a-zA-Z0-9_]+)/$',  
                            'donomo.archive.account.account_views.account_detail',
                            name='account-detail'),
 
# payment_views
                       url(r'^pay/return/$', 
                            'donomo.archive.account.payment_views.request_payment_return'),

                       url(r'^pay/cancel/$', 
                            'donomo.archive.account.payment_views.request_payment_cancel'),

                       # a POST to this URL sends a signal
                       # handled in donomo.archive.account.on_payment_complete
                       url(r'^pay/ipn/gpxjyxmrzzqpncosnbenvkkzcmxz/$', 
                            include('paypal.standard.ipn.urls')), 
                        
                       url(r'^pay/$',  
                            'donomo.archive.account.payment_views.request_payment_standard'),
                            
                       url(r'^paypro/$',  
                            'donomo.archive.account.payment_views.request_payment_pro'),

                       url(r'^(?P<username>[-+@.a-zA-Z0-9_]+)/refill/$',  
                            'donomo.archive.account.payment_views.account_refill',
                            name='account-refill'),

                       url(r'^(?P<username>[-+@.a-zA-Z0-9_]+)/subscribe/$',  
                            'donomo.archive.account.payment_views.account_subscribe',
                            name='account-subscribe'),
                           
                       url(r'^$',
                           'donomo.archive.account.account_views.account_detail'),
                )
                        
