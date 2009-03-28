from paypal.standard.signals import payment_was_successful

def on_payment_complete(ipn, **kwargs):
    u = Users.objects.get(email=ipn.payer_email)
    u.groups.add(Group.objects.create(name=ipn.mc_gross)) #TODO create an Account model

payment_was_successful.connect(on_payment_complete)
