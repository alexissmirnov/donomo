from paypal.standard.signals import payment_was_successful
import logging
logging = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


def on_payment_complete(ipn, **kwargs):
    u = Users.objects.get(email=ipn.payer_email)
    logging.info('credit user %s with %s' % ( u, ipn))
    #u.groups.add(Group.objects.create(name=ipn.mc_gross)) #TODO create an Account model

payment_was_successful.connect(on_payment_complete)
