from django.db                           import models
from django.contrib.auth.models          import User

class Invoice(models.Model):
    owner = models.ForeignKey(
        User,
        unique = True,
        null   = False)

class Account(models.Model):
    PROCUDT_CREDIT_CARGE = {'OCR': 10}
    USD_TO_CREDITS = 1000

    
    owner = models.ForeignKey(
        User,
        unique = True,
        null   = False)
    balance = models.IntegerField()
    
    def expense(product, owner):
        account = Account.objects.get(owner = owner)
        balance = account.balance - PAccount.ROCUDT_CREDIT_CARGE[product]
    
        if balance > 0:
            account.balance = balance
            account.save()
            return True
        else:
            return False
