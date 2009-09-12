from django.http                            import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.conf                            import settings
from django.contrib                         import auth
from django.contrib.auth.decorators         import login_required
from django.shortcuts                       import render_to_response
from django.template                        import RequestContext
from django.core.urlresolvers               import reverse
from django                                 import forms
from django.utils.translation               import ugettext_lazy as _
from django.contrib.auth.models             import User
from registration.models                    import RegistrationProfile
from donomo.archive.models                  import Page, Document
from donomo.billing.models                  import Account, Invoice
from donomo.archive.api                     import api_impl
from recaptcha                              import RecaptchaForm, RecaptchaFieldPlaceholder, RecaptchaWidget
import os
import logging
logging = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])

def trial(request):
    if request.method == 'GET':
        return render_to_response('account/trial.html',
                                  context_instance = RequestContext(request))
    elif request.method == 'POST':
        if not request.POST.has_key('email'):
            return HttpResponseBadRequest('no email') #TODO: validation

        try:
            user, created = get_or_create_trial_account(request.POST['email'])
            
            if not created:
                return HttpResponseForbidden("Trial for %s has expired" % user.email)
            
            # now that the user object is created, submit the files for processing                    
            api_impl.process_uploaded_files(request.FILES, user)
                
        except Exception, e:
            print str(e);
        return HttpResponse('User created: ' + str(created))
    else:
        return HttpResponse('method not supported')

def get_or_create_trial_account(email):
    try:
        return (User.objects.get(email__exact = email), False)
    except User.DoesNotExist:
        user = User.objects.create_user(email, email)
        user.set_unusable_password()
        user.is_active = False
        user.save()
        return (user, True)


@login_required()
def account_delete(request, username):
    """
    Deletes user's account.
    """
    #TODO: delete all user's data on solr, s3, etc.
    if request.user.is_authenticated() and username == user:
        request.user.delete()
        return logout(request)
    else:
        return HttpResponse('forbidden')

def signin(request):
    username = request.POST['username']
    password = request.POST['password']
    user = auth.authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect('/')
        else:
            return render_to_response('account/account_disabled.html')
    else:
        return render_to_response('account/invalid_login.html', locals())

@login_required()
def logout(request):
    logging.debug(RequestContext(request))

    return auth.logout(request,
                       next_page=request.REQUEST.get('next', None),
                       template_name = RequestContext(request)['template_name'])

def account_detail(request, username = None):
    if request.method == 'HEAD':
        return head_account_detail(request, username)
    elif request.method == 'GET':
        return get_account_detail(request, username)
    
def head_account_detail(request, username = None):
    """
    Returns HttpResponse 200 if the account exists, 404 otherwise. 
    Used to verify the existence of the account.
    Can be invoked by anonymous request.
    """
    response = HttpResponse(content_type = 'text/plain')
    try:
        user = User.objects.get(username__exact = username)
        response['donomo-account-active'] = user.is_active
    except User.DoesNotExist:
        response.status_code = 404
        
    return response

@login_required()
def get_account_detail(request, username = None):
    """
        Renders account management UI
    """
    #TODO replace with generic views once
    #http://code.djangoproject.com/ticket/3639 is resolved

    if username is not None and username != request.user.username:
        return HttpResponse('forbidden: username %s' % username)

    if request.method == 'GET':
        page_count = Page.objects.filter(owner = request.user).count()
        document_count = Document.objects.filter(owner = request.user).count()

        return render_to_response('account/userprofile_form.html',
                                  {'page_count' : page_count,
                                   'document_count': document_count,
                                   'remaining_storage_days' : "30" },
                                  context_instance = RequestContext(request))
    else:
        return HttpResponse('forbidden')

@login_required()
def account_export(request, username):
    """
        Renders account management UI
    """
    #TODO replace with generic views once
    #http://code.djangoproject.com/ticket/3639 is resolved

    if username != request.user.username and not request.user.staff:
        return HttpResponse('forbidden: username %s' % username)

    if request.method == 'GET':
       return HttpResponse('Not implemented yet')
    else:
       return HttpResponse('forbidden')


# I put this on all required fields, because it's easier to pick up
# on them with CSS or JavaScript if they have a class of "required"
# in the HTML. Your mileage may vary. If/when Django ticket #3515
# lands in trunk, this will no longer be necessary.
attrs_dict = { 'class': 'required' }

class RegistrationForm(RecaptchaForm):
    """
    Form for registering a new user account.

    Requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should either preserve the base ``save()`` or implement
    a ``save()`` which accepts the ``profile_callback`` keyword
    argument and passes it through to
    ``RegistrationProfile.objects.create_inactive_user()``.

    """
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_(u'Email address (must already exist)'),
                             help_text=_(u"You'll use this address to log in Donomo. We'll use this address to send you notifications when your documents are processed. We will never share it with third parties without your permission."))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_(u'Enter Password'))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_(u'Retype Password'))

    captcha = RecaptchaFieldPlaceholder(widget=RecaptchaWidget(theme='white'),
                                        label=_(u'Word Verification'),
                                        help_text=_(u"Type the characters you see in the picture"))

    def clean_username(self):
        """
        Validate that the email is not already
        in use.

        """
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email']
        raise forms.ValidationError(_(u'This email is already registered. Please choose another.'))

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_(u'You must type the same password each time'))
        return self.cleaned_data

    def save(self, profile_callback=None):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User``.

        This is essentially a light wrapper around
        ``RegistrationProfile.objects.create_inactive_user()``,
        feeding it the form data and a profile callback (see the
        documentation on ``create_inactive_user()`` for details) if
        supplied.

        """
        new_user = RegistrationProfile.objects.create_inactive_user(
                        username=self.cleaned_data['email'],
                        password=self.cleaned_data['password1'],
                        email=self.cleaned_data['email'],
                        profile_callback=profile_callback)
        return new_user

class SiteProfileNotAvailable(Exception):
    pass

def create_profile_model(user):
    """
    This method is supplied as "profile_callback" and will be called just after the
    new user object object is created.
    """
    from django.db import models
    from django.core.exceptions import ImproperlyConfigured
    if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
        raise SiteProfileNotAvailable

    try:
        app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
        model = models.get_model(app_label, model_name)
        profile, created = model._default_manager.get_or_create(
                                user=user,
                                defaults={"balance": Account.BALANCE_ON_CREATION })
        logging.debug("%s is created? %s" %(profile, created))

        return profile
    except (ImportError, ImproperlyConfigured):
        raise SiteProfileNotAvailable
    
def register(request,
             success_url=None,
             form_class = RegistrationForm,
             profile_callback=create_profile_model,
             template_name='registration/registration_form.html',
             extra_context=None):
    """
    Allow a new user to register an account.

    Following successful registration, issue a redirect; by default,
    this will be whatever URL corresponds to the named URL pattern
    ``registration_complete``, which will be
    ``/accounts/register/complete/`` if using the included URLConf. To
    change this, point that named pattern at another URL, or pass your
    preferred URL as the keyword argument ``success_url``.

    By default, ``registration.forms.RegistrationForm`` will be used
    as the registration form; to change this, pass a different form
    class as the ``form_class`` keyword argument. The form class you
    specify must have a method ``save`` which will create and return
    the new ``User``, and that method must accept the keyword argument
    ``profile_callback`` (see below).

    To enable creation of a site-specific user profile object for the
    new user, pass a function which will create the profile object as
    the keyword argument ``profile_callback``. See
    ``RegistrationManager.create_inactive_user`` in the file
    ``models.py`` for details on how to write this function.

    By default, use the template
    ``registration/registration_form.html``; to change this, pass the
    name of a template as the keyword argument ``template_name``.

    **Required arguments**

    None.

    **Optional arguments**

    ``form_class``
        The form class to use for registration.

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``profile_callback``
        A function which will be used to create a site-specific
        profile instance for the new ``User``.

    ``success_url``
        The URL to redirect to on successful registration.

    ``template_name``
        A custom template to use.

    **Context:**

    ``form``
        The registration form.

    Any extra variables supplied in the ``extra_context`` argument
    (see above).

    **Template:**

    registration/registration_form.html or ``template_name`` keyword
    argument.

    """
    remote_ip = request.META['REMOTE_ADDR']

    if request.method == 'POST':
        form = form_class(remote_ip, data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = form.save(profile_callback=profile_callback)
            # success_url needs to be dynamically generated here; setting a
            # a default value using reverse() will cause circular-import
            # problems with the default URLConf for this application, which
            # imports this file.
            return HttpResponseRedirect(success_url or reverse('registration_complete'))
    else:
        form = form_class(remote_ip)

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(template_name,
                              { 'form': form },
                              context_instance=context)

