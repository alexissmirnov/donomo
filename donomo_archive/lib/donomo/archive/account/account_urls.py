from django.conf.urls.defaults                  import patterns
from donomo.archive.account.account_views       import on_openid_signin

urlpatterns = patterns('',
    (r'^signin/$', 'django_openidconsumer.views.begin', {
        'sreg': 'email,nickname' ,
    }),
    (r'^signin/complete/$', 'django_openidconsumer.views.complete', {
        'on_success': on_openid_signin,
        }),
    (r'^signout/$', 'donomo.archive.account.account_views.signout'),
    (r'^delete/$', 'donomo.archive.account.account_views.delete'),
    (r'^(?P<username>\w+)/$', 'donomo.archive.account.account_views.account_detail'),
)
