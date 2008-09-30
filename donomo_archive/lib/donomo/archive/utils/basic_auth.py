"""decorator providing HTTP Basic Auth on per-view basis based on 
http://www.djangosnippets.org/snippets/243/
"""
# pylint: disable-msg=W0142
# pylint: disable-msg=R0913
import base64
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.conf import settings

def view_or_basicauth(view,
                      request,
                      test_func,
                      methods,
                      realm,
                      *args,
                      **kwargs):
    """
    This is a helper function used by both 'logged_in_or_basicauth' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """
    if test_func(request.user) or not (request.method in methods):
        # Already logged in, or auth check disabled, or request's method isn't
        # specified as being needed auth
        # then just return the view.
        return view(request, *args, **kwargs)

    # They are not logged in. See if they provided login credentials
    #
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            # NOTE: We are only support basic authentication for now.
            #
            if auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        request.user = user
                        return view(request, *args, **kwargs)

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    #
    response = HttpResponse()
    response.status_code = 401
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    return response
    
#############################################################################
#
def logged_in_or_basicauth(methods = ('GET', 'PUT', 'POST', 'DELETE', 'HEAD'),
                           realm = settings.BASIC_AUTH_REALM):
    """
    A simple decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.

    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.

    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.

    The uses for this are for urls that are access programmatically such as
    by API clients, yet the view requires a user to be logged in. 

    Use is simple:

    @logged_in_or_basicauth
    def your_view:
        ...

    You can provide the name of the realm to ask for authentication within.
    """
    #pylint: disable-msg=C0111
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.is_authenticated(),
                                     methods, realm, *args, **kwargs)
        return wrapper
    return view_decorator   
    #pylint: enable-msg=C0111

#############################################################################
#
def has_perm_or_basicauth(perm,
                          methods = ('GET', 'PUT', 'POST', 'DELETE', 'HEAD'),
                          realm = settings.BASIC_AUTH_REALM):
    """
    This is similar to the above decorator 'logged_in_or_basicauth'
    except that it requires the logged in user to have a specific
    permission.

    Use:

    @logged_in_or_basicauth('asforums.view_forumcollection')
    def your_view:
        ...

    """
    #pylint: disable-msg=C0111
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.has_perm(perm),
                                     methods, realm, *args, **kwargs)
        return wrapper
    return view_decorator

