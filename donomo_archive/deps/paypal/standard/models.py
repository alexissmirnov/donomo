#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings

from paypal.standard.signals import payment_was_successful, payment_was_flagged

# ### ToDo: would be cool if PayPalIPN.query was a JSON field
# ### or something else that let you get at the data better.

# ### ToDo: Should the signal be in `set_flag` or `verify`?

# ### ToDo: There are a # of fields that appear to be duplicates from PayPal
# ### can we sort them out?

# ### Todo: PayPalIPN choices fields? in or out?

POSTBACK_ENDPOINT = "https://www.paypal.com/cgi-bin/webscr"
SANDBOX_POSTBACK_ENDPOINT = "https://www.sandbox.paypal.com/cgi-bin/webscr"


class PayPalIPN(models.Model):
    """
    Logs PayPal IPN interactions.
    
    """    
    # 20:18:05 Jan 30, 2009 PST - PST timezone support is not included out of the box.
    # PAYPAL_DATE_FORMAT = ("%H:%M:%S %b. %d, %Y PST", "%H:%M:%S %b %d, %Y PST",)
    # PayPal dates have been spotted in the wild with these formats, beware!
    PAYPAL_DATE_FORMAT = ("%H:%M:%S %b. %d, %Y PST",
                          "%H:%M:%S %b. %d, %Y PDT",
                          "%H:%M:%S %b %d, %Y PST",
                          "%H:%M:%S %b %d, %Y PDT",)
    
    # FLAG_CODE_CHOICES = (
    # PAYMENT_STATUS_CHOICES = "Canceled_ Reversal Completed Denied Expired Failed Pending Processed Refunded Reversed Voided".split()
    # AUTH_STATUS_CHOICES = "Completed Pending Voided".split()
    # ADDRESS_STATUS_CHOICES = "confirmed unconfirmed".split()
    # PAYER_STATUS_CHOICES = "verified / unverified".split()
    # PAYMENT_TYPE_CHOICES =  "echeck / instant.split()
    # PENDING_REASON = "address authorization echeck intl multi-currency unilateral upgrade verify other".split()
    # REASON_CODE = "chargeback guarantee buyer_complaint refund other".split()
    # TRANSACTION_ENTITY_CHOICES = "auth reauth order payment".split()

    # Buyer information.
    address_city = models.CharField(max_length=40, blank=True)
    address_country = models.CharField(max_length=64, blank=True)
    address_country_code = models.CharField(max_length=64, blank=True, help_text="ISO 3166")
    address_name = models.CharField(max_length=128, blank=True)
    address_state = models.CharField(max_length=40, blank=True)
    address_status = models.CharField(max_length=11, blank=True)
    address_street = models.CharField(max_length=200, blank=True)
    address_zip = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, blank=True)
    payer_business_name = models.CharField(max_length=127, blank=True)
    payer_email = models.CharField(max_length=127, blank=True)
    payer_status= models.CharField(max_length=32, blank=True)
    payer_id = models.CharField(max_length=13, blank=True)
    payer_status = models.CharField(max_length=10, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    residence_country = models.CharField(max_length=2, blank=True)

    # Basic information.
    business = models.CharField(max_length=127, blank=True, help_text="Email where the money was sent.")
    item_name = models.CharField(max_length=127, blank=True)
    item_number = models.CharField(max_length=127, blank=True)
    quantity = models.IntegerField(blank=True, default=1, null=True)
    receiver_email = models.EmailField(max_length=127, blank=True)
    receiver_id = models.CharField(max_length=127, blank=True)  # 258DLEHY2BDK6

    # Merchant specific.
    custom = models.CharField(max_length=255, blank=True)
    invoice = models.CharField(max_length=127, blank=True)
    memo = models.CharField(max_length=255, blank=True)
    
    # Website payments standard.
    auth_id = models.CharField(max_length=19, blank=True)
    auth_exp = models.CharField(max_length=28, blank=True)
    auth_amount = models.FloatField(default=0, blank=True, null=True)
    auth_status = models.CharField(max_length=9, blank=True) 
    mc_gross = models.FloatField(default=0, blank=True, null=True)
    mc_fee = models.FloatField(default=0, blank=True, null=True)
    mc_currency = models.CharField(max_length=32, default="USD", blank=True)
    currency_code = models.CharField(max_length=32, default="USD", blank=True)
    payment_cycle= models.CharField(max_length=32, blank=True) #Monthly
    payment_fee = models.FloatField(default=0, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True, help_text="HH:MM:SS DD Mmm YY, YYYY PST")
    payment_status = models.CharField(max_length=9, blank=True)
    payment_type = models.CharField(max_length=7, blank=True)
    pending_reason = models.CharField(max_length=14, blank=True)
    reason_code = models.CharField(max_length=15, blank=True)
    transaction_entity = models.CharField(max_length=7, blank=True)
    txn_id = models.CharField("Transaction ID", max_length=19, blank=True, help_text="PayPal transaction ID.")
    txn_type = models.CharField("Transaction Type", max_length=128, blank=True, help_text="PayPal transaction type.")
    parent_txn_id = models.CharField("Parent Transaction ID", max_length=19, blank=True)

    # Recurring Payments:
    profile_status = models.CharField(max_length=32, blank=True) 
    initial_payment_amount = models.FloatField(default=0, blank=True, null=True)
    amount_per_cycle = models.FloatField(default=0, blank=True, null=True)
    outstanding_balance = models.FloatField(default=0, blank=True, null=True)
    period_type = models.CharField(max_length=32, blank=True)
    product_name = models.CharField(max_length=128, blank=True)
    product_type= models.CharField(max_length=128, blank=True)
    recurring_payment_id = models.CharField(max_length=128, blank=True)  # I-FA4XVST722B9
    receipt_id= models.CharField(max_length=64, blank=True)  # 1335-7816-2936-1451
    next_payment_date = models.DateTimeField(blank=True, null=True, help_text="HH:MM:SS DD Mmm YY, YYYY PST")

    # Additional information - full IPN query and time fields.
    test_ipn = models.BooleanField(default=False, blank=True)
    ipaddress = models.IPAddressField(blank=True)
    flag = models.BooleanField(default=False, blank=True)
    flag_code = models.CharField(max_length=16, blank=True)
    flag_info = models.TextField(blank=True)
    query = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "paypal_ipn"
        verbose_name = "PayPal IPN"

    def __unicode__(self):
        fmt = u"<IPN: %s %s>"
        if self.is_transaction():
            return fmt % ("Transaction", self.txn_id)
        else:
            return fmt % ("Recurring", self.recurring_payment_id)
        
    def is_transaction(self):
        return len(self.txn_id) > 0
    
    def is_recurring(self):
        return len(self.recurring_payment_id) > 0
        
    def _postback(self, test=True):
        """
        Perform PayPal Postback validation.
        Sends the received data back to PayPal which responds with verified or invalid.
        Flags the payment if the response is invalid.
        Returns True if the postback is verified.
        
        """
        import urllib2
        if test:
            endpoint = SANDBOX_POSTBACK_ENDPOINT
        else:
            endpoint = POSTBACK_ENDPOINT
        response = urllib2.urlopen(endpoint, "cmd=_notify-validate&%s" % self.query).read()
        if response == "VERIFIED":
            return True
        else:
            self.set_flag("Invalid postback.")
            return False
                    
    def verify(self, item_check_callable=None, test=True):
        """
        Verifies an IPN.
        Checks for obvious signs of weirdness in the payment and flags appropriately.
        
        Provide a callable that takes a PayPalIPN instances as a parameters and returns
        a tuple (True, Non) if the item is valid. Should return (False, "reason") if the
        item isn't valid. This function should check that `mc_gross`, `mc_currency`
        `item_name` and `item_number` are all correct.

        """
        from paypal.standard.helpers import duplicate_txn_id
        
        if self._postback(test):

            if self.is_transaction():
                if self.payment_status != "Completed":
                    self.set_flag("Invalid payment_status.")
                if duplicate_txn_id(self):
                    self.set_flag("Duplicate transaction ID.")
                if self.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
                    self.set_flag("Invalid receiver_email.")
                if callable(item_check_callable):
                    flag, reason = item_check_callable(self)
                    if flag:
                        self.set_flag(reason)                 

            else:
                # ### To-Do: Need to run a different series of checks on recurring payments.
                pass
    
        if self.flag:
            payment_was_flagged.send(sender=self)
        else:
            payment_was_successful.send(sender=self)

    def verify_secret(self, form_instance, secret):
        """
        Verifies an IPN payment over SSL using EWP. 
        
        """
        from paypal.standard.helpers import check_secret
        if not check_secret(form_instance, secret):
            self.set_flag("Invalid secret.")

    def init(self, request):
        self.query = request.POST.urlencode()
        self.ipaddress = request.META.get('REMOTE_ADDR', '')
    
    def set_flag(self, info, code=None):
        """
        Sets a flag on the transaction and also sets a reason.
        
        """
        self.flag = True
        self.flag_info += info
        if code is not None:
            self.flag_code = code
    

class PayPalIPNExtended(PayPalIPN):
    """
    Idea for extending the PayPalIPN class to include other tasty IPN variables.

    """
    # ### To-do: Unimplemnted fields that you mightw want to think about.
    # mc_handling
    # mc_shipping
    # num_cart_items
    # option_name1
    # option_name2
    # option_selection1_x
    # option_selection2_x
    # shipping_method
    # shipping
    # tax
    
    
    # Advanced and custom information.
    # option_name_1
    # option_name_2
    # option_selection1
    # option_selection2
    # tax
    
    # Refund info.
    
    # Currency and currency exchange.
    
    # Auctions.
    
    # Mass payment.
    
    # Subscription variables.
    
    # Dispute notifications.
    
    class Meta:
        abstract = True