from paypal.standard.ipn.signals    import payment_was_successful, payment_was_flagged
from donomo.billing.models          import Account, Invoice
from django.contrib.auth.models     import User

import os
import logging
logging = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


def on_payment_successful(ipn, **kwargs):
    logging.info('payment complete : %s' % kwargs)
    invoice = Invoice.objects.get(pk = ipn.invoice)
    account = Account.objects.get_or_create(owner = invoice.owner, defaults={'balance' : 0})[0]
    
    if ipn.payment_status == 'Completed':
        account.balance = account.balance + Account.USD_TO_CREDITS * float(ipn.mc_gross)
        account.save()
    
payment_was_successful.connect(on_payment_successful)


def on_payment_flagged(ipn, **kwargs):
    logging.info('payment flagged : %s' % kwargs)
    
payment_was_flagged.connect(on_payment_flagged)
