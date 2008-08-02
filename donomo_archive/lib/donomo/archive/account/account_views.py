from django.http                            import HttpResponse
from django.contrib.auth.models             import User
from django.contrib.auth                    import authenticate, login, logout

from django_openidconsumer.views            import signout as openid_signout
from django_openidconsumer.views            import default_on_success
from django.contrib.auth.decorators         import login_required

from django.shortcuts                       import render_to_response

#
# pylint: disable-msg = E1101
#
#   E1101 : Class 'User' has no 'DoesNotExist' member
#

def on_openid_signin(request, identity_url, openid_response):
    sreg = openid_response.extensionResponse('sreg')

    email = sreg.get('email', 'undisclosed')
    
    identity_url_cleaned = identity_url.strip().replace('http://','').replace('https://','')
    import re
    match_non_alnum = re.compile("[^a-zA-Z0-9]+")

    identity_url_cleaned = match_non_alnum.sub(' ', identity_url_cleaned).strip().replace(' ', '_')

    try:
        user = User.objects.get(username=identity_url_cleaned)
    except User.DoesNotExist:
        user = User.objects.create_user(identity_url_cleaned, email, '')
    
    user = authenticate(username=identity_url_cleaned)
    if user:
        login(request, user)
        return default_on_success(request, identity_url, openid_response)
    else:
        return None #todo
    
def delete(request):
    if request.user.is_authenticated():
        request.user.delete()
        logout(request)
        return openid_signout(request)    
    else:
        return HttpResponse('forbidden')
    
def signout(request):
    print str(request.user)
    logout(request)
    print str(request.user)
    return openid_signout(request)    

@login_required()    
def account_detail(request, username):
    #TODO replace with generic views once
    #http://code.djangoproject.com/ticket/3639 is resolved
    
    if username != request.user.username:
        return HttpResponse('forbidden: username %s' % username)
    
    if request.method == 'GET':
        return render_to_response('account/userprofile_form.html', {'user' : request.user})
    else:
        return HttpResponse('forbidden')