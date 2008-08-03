from django.conf.urls.defaults                  import patterns, url
from donomo.archive.account.account_views       import on_openid_signin

urlpatterns = patterns('',
    url(r'^signin/$', 
        'django_openidconsumer.views.begin',     
        {'sreg': 'email,nickname'},
        name='signin',
        ),
    
    url(r'^signin/complete/$', 
        'django_openidconsumer.views.complete', 
        {'on_success': on_openid_signin},
        name='signin-complete',
        ),
    
    url(r'^signout/$', 
        'donomo.archive.account.account_views.signout',
        name='signout'),
    
    url(r'^delete/$', 
        'donomo.archive.account.account_views.delete',
        name='account-delete'),
        
    url(r'^(?P<username>\w+)/$', 
        'donomo.archive.account.account_views.account_detail',
        name='account-detail'),
)
