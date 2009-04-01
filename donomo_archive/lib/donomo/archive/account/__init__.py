from paypal.standard.signals    import payment_was_successful
from donomo.billing.models      import Account
from django.contrib.auth.models import User

import os
import logging
logging = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


def on_payment_complete(**kwargs):
    logging.info('payment complete : %s' % kwargs)
    ipn = kwargs['sender']
    u = User.objects.get(email=ipn.payer_email)
    account = Account.objects.get_or_create(owner = u)[0]
    
    if ipn.payment_status == 'Completed':
        account.balance = account.balance + Account.USD_TO_CREDITS * float(ipn.mc_gross)
        account.save()
    
payment_was_successful.connect(on_payment_complete)
