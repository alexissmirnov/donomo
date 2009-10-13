from django.db                           import models
from django.contrib.auth.models          import User

PRICING_PLANS = {'payg1' : [29.99, 1000, 30000], 
                  'payg2' : [99.95, 4000, 120000],
                  'plus' : [30.00, 1500, 45000],
                  'pro' : [90.00, 5000, 150000],
                  'max' : [300.00, 17000, 510000] }



def get_remaining_credit(user, billable_event = 'ocr.ocropus.page'):
    """
    Returns the amount of billable events that the account can perform,
    based on available credit.
    
    Eg. if a billable event is OCRing one page with orcopus, the return
    is a count of pages that a user can process with remaining account
    balance.
    
    For inactive (trial) account, return 1 meaning "have enough credit to
    perform one billable event"
    """
    if user.is_active:
        account = Account.objects.get(user = user)
        return account.prepaid_product_ocr()
    else:
        # For trial account, return enough credits to perform one billable event
        return 1
    
def change(user, charge):
    """
    Charges a user a given number of credits.
    Returns True is the charge was successful.
    """
    
    # TODO: wrap in a transaction
    account = Account.objects.get(user = user)
    return charge_account(account, charge)

def charge_account(account, charge):
    """
    Charges an account object a given number of credits.
    Returns True is the charge was successful.
    
    Charge is measured in "credits". Balance is measured in credits
    """
    balance = account.balance - charge
    
    if balance > 0:
        account.balance = balance
        account.save()
        return True
    else:
        return False


def refill_account( account, usd, purchace_plan = None):
    """
    Adds credits to an account based on the given purchase plan
    """
    if purchace_plan is None:
        if usd == 29.99:
            purchace_plan = 'payg1'
        elif usd == 99.98:
            purchace_plan = 'payg2'
        elif usd == 30:
            purchace_plan = 'plus'
        elif usd == 90:
            purchace_plan = 'pro'
        elif usd == 300:
            purchace_plan = 'max'
        else:
            return
    
    gross, pages, credit = PRICING_PLANS[purchace_plan]
    account.balance = account.balance + credit
    account.save()
    
def process_billable_event(user, event_name):
    """
    This function will perform a charge that corresponds to the
    billable event done by a given user.
    How much each billable event costs is determined by a table in
    Account class.
    """
    account = Account.objects.get(user = user)
    charge = Account.PRODUCT_CREDIT_CARGE[event_name]
    return charge_account(account, charge)


class Invoice(models.Model):
    owner = models.ForeignKey(
        User,
        null   = False)

class Account(models.Model):
    PRODUCT_CREDIT_CARGE = {'ocr.ocropus.page': 30}
    BALANCE_ON_CREATION = 5.00

    
    user = models.ForeignKey(
        User,
        unique = True,
        null   = False)
    balance = models.IntegerField()
    
    def prepaid_product_ocr(self):
        return max(0, self.balance) / float(Account.PRODUCT_CREDIT_CARGE['ocr.ocropus.page'])