from paypal.standard.ipn.signals    import payment_was_successful, payment_was_flagged
from paypal.standard.models         import ST_PP_COMPLETED
from django.contrib.auth.models     import User
import donomo.billing.models

import os
import logging
logging = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


def on_payment_successful(sender, **kwargs):
    logging.info('payment complete : %s status=%s' % (kwargs, sender.payment_status))
    invoice = donomo.billing.models.Invoice.objects.get(pk = sender.invoice)
    account = donomo.billing.models.Account.objects.get_or_create(owner = invoice.owner, defaults={'balance' : 0})[0]
    if sender.payment_status == ST_PP_COMPLETED:
        # TODO pass purchase plan code via the payment object instead of
        # having refill_account figure it out based on the gross amount
        donomo.billing.models.refill_account(account, float(sender.mc_gross))

payment_was_successful.connect(on_payment_successful)


def on_payment_flagged(sender, **kwargs):
    logging.info('payment flagged : %s flag=%s, payment_status=%s' % (kwargs, sender.flag, sender.payment_status))
payment_was_flagged.connect(on_payment_flagged)
