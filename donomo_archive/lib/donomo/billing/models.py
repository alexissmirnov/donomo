from django.db                           import models
from django.contrib.auth.models          import User

class Invoice(models.Model):
    owner = models.ForeignKey(
        User,
        null   = False)

class Account(models.Model):
    PRODUCT_CREDIT_CARGE = {'OCR': 15}
    USD_TO_CREDITS = 500
    BALANCE_ON_CREATION = 5.00

    
    user = models.ForeignKey(
        User,
        unique = True,
        null   = False)
    balance = models.IntegerField()
    
    def prepaid_product_ocr(self):
        return ( self.balance * Account.USD_TO_CREDITS ) / Account.PRODUCT_CREDIT_CARGE['OCR']