from django.db                           import models
from django.contrib.auth.models          import User

class Invoice(models.Model):
    owner = models.ForeignKey(
        User,
        null   = False)

class Account(models.Model):
    PRODUCT_CREDIT_CARGE = {'OCR': 5}
    USD_TO_CREDITS = 1000

    
    owner = models.ForeignKey(
        User,
        unique = True,
        null   = False)
    balance = models.IntegerField()
    
def expense(product, owner):
    try:
        account = Account.objects.get(owner = owner)
    except:
        return True # Everything's free for non-account holders!
    
    balance = account.balance - Account.PRODUCT_CREDIT_CARGE[product]

    if balance > 0:
        account.balance = balance
        account.save()
        return True
    else:
        return False
        