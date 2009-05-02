#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from paypal.standard.ipn.forms import PayPalIPNForm
from paypal.standard.ipn.models import PayPalIPN

import logging
import os
logging = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])

@require_POST
def ipn(request, item_check_callable=None):
    """
    PayPal IPN endpoint (notify_url).
    Used by both PayPal Payments Pro and Payments Standard to confirm transactions.
    http://tinyurl.com/d9vu9d
    
    PayPal IPN Simulator:
    https://developer.paypal.com/cgi-bin/devscr?cmd=_ipn-link-session
    
    """    
    
    logging.info(request)
    
    form = PayPalIPNForm(request.POST)
    
    logging.info(form)
    logging.info(form.is_valid())
    
    if form.is_valid():
        try:
            ipn_obj = form.save(commit=False)
            logging.info(ipn_obj)
        except Exception, e:
            logging.error(e)
            ipn_obj = PayPalIPN()
            ipn_obj.set_flag("Exception while processing. (%s)" % form.errors)
            logging.info(ipn_obj)
    else:
        ipn_obj.set_flag("Invalid form. (%s)" % form.errors)
        logging.info(ipn_obj)
        
    ipn_obj.initialize(request)
    
    logging.info(ipn_obj.flag)
    logging.info(request.is_secure())
    logging.info(request.GET)
    logging.info('secret' in request.GET)
    
    if not ipn_obj.flag:
        # Secrets should only be used over SSL.
        if request.is_secure() and 'secret' in request.GET:
            logging.info('request is secured')
            ipn_obj.verify_secret(form, request.GET['secret'])
        else:
            logging.info('request NOT secured')
            ipn_obj.verify(item_check_callable)

    ipn_obj.save()
    logging.info(ipn_obj)
    logging.info('ipn DONE')
    return HttpResponse("OKAY")