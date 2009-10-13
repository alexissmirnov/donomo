from django.http                            import HttpResponse, HttpResponseRedirect
from django.conf                            import settings
from django.contrib                         import auth
from django.contrib.auth.decorators         import login_required
from django.shortcuts                       import render_to_response
from django.template                        import RequestContext
from django.core.urlresolvers import reverse
from django                                 import forms
from django.utils.translation               import ugettext_lazy as _
from django.contrib.auth.models             import User
from registration.models                    import RegistrationProfile
from donomo.archive.models                  import Page, Document
from donomo.billing.models                  import Account, Invoice, PRICING_PLANS
from paypal.pro.views import PayPalPro
from paypal.standard.forms import PayPalEncryptedPaymentsForm # PayPalSharedSecretEncryptedPaymentsForm
import time

import os
import logging
logging = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])

@login_required()
def account_refill(request, username):
    """
    View that adds funds to an account. Renders Paypal button.
    """
    plan = request.GET['payg_plan']
    if not plan in ['payg1', 'payg2']:
        return HttpResponse('wrong payment plan')

    amount, pages, credit = PRICING_PLANS[plan]
    
    return render_to_response('account/refill.html',
                              {
                               'amount' : amount,
                               'plan_pages' : pages,
                               'pay_button' : render_payment_standard_button(request.user, amount)
                               },
                               context_instance = RequestContext(request))

@login_required()
def account_subscribe(request, username):
    """
    View that adds funds to an account. Renders Paypal button.
    """
    plan = request.GET['plan']
    
    if not plan in ['max', 'pro', 'plus']:
        return HttpResponse('wrong subscription plan')
    
    amount, pages, credit = PRICING_PLANS[plan]
    button = render_subscription_button(request.user, amount)
    
    return render_to_response('account/subscribe.html',
                              {
                               'plan' : plan,
                               'plan_subscription_amount' : amount,
                               'plan_pages' : pages,
                               'amount' : amount,
                               'pay_button' : button
                               },
                               context_instance = RequestContext(request))

###############################################################################



def request_payment_return(request):
    logging.info(request)
    return HttpResponseRedirect('/')

def request_payment_cancel(request):
    logging.info(request)
    return HttpResponseRedirect('/')

def request_payment_standard(request):
    return HttpResponse(render_payment_standard_button(request.user))

def render_payment_standard_button(owner, amount = "10.00"):
    logging.info('rendering standard payment button. sandbox? %d' % settings.PAYPAL_TEST)

    # What you want the button to do.
    invoice = Invoice(owner = owner, pk = int(time.time()))
    invoice.save()

    #TODO remove hardcoded URLs and domain name
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": amount,
        "item_name": "On-demand OCR",
        "invoice": str(invoice.pk),
        "notify_url": "https://archive.donomo.com/account/pay/ipn/gpxjyxmrzzqpncosnbenvkkzcmxz/",
        "return_url": "https://archive.donomo.com/account/pay/return/",
        "cancel_return": "https://archive.donomo.com/account/pay/cancel/",
    }

    # Create the instance.
    form = PayPalEncryptedPaymentsForm(initial=paypal_dict) #PayPalSharedSecretEncryptedPaymentsForm(initial=paypal_dict)


    # Output the button.
    result = form.render()

    return result

def render_subscription_button(owner, amount):
    # What you want the button to do.
    paypal_dict = {
        "cmd": "_xclick-subscriptions",
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "a3": amount,                      # monthly price 
        "p3": 1,                           # duration of each unit (depends on unit)
        "t3": "M",                         # duration unit ("M for Month")
        "src": "1",                        # make payments recur
        "sra": "1",                        # reattempt payment on payment error
        "no_note": "1",                    # remove extra notes (optional)
        "item_name": "Cloud OCR subscription",
        "notify_url": "https://archive.donomo.com/account/pay/ipn/gpxjyxmrzzqpncosnbenvkkzcmxz/",
        "return_url": "https://archive.donomo.com/account/pay/return/",
        "cancel_return": "https://archive.donomo.com/account/pay/cancel/",
    }

    # Create the instance.
    form = PayPalEncryptedPaymentsForm(initial=paypal_dict, button_type="subscribe")


    # Output the button.
    result = form.render()

    return result


def request_payment_pro(request):
    item = {'amt':"10.00",              # amount to charge for item
            'inv':"inventory#",         # unique tracking variable paypal
            'custom':"tracking#",       # custom tracking variable for you
            'cancelurl':"https://www.donomo.com/account/pay/cancel/",   # Express checkout cancel url
            'returnurl':"https://www.donomo.com/account/pay/return/"}   # Express checkout return url

    kw = {'item':'item',                        # what you're selling
       'payment_template': 'template',          # template to use for payment form
       'confirm_template': 'confirm_template',  # form class to use for Express checkout confirmation
       'payment_form_cls': 'payment_form_cls',  # form class to use for payment
       'success_url': '/success',               # where to redirect after successful payment
       }
    ppp = PayPalPro(**kw)
    return HttpResponse(ppp.render_payment_form())



