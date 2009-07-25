from django.db                           import models
from django.contrib.auth.models          import User

class Invoice(models.Model):
    owner = models.ForeignKey(
        User,
        null   = False)

class Account(models.Model):
    PRODUCT_CREDIT_CARGE = {'OCR': 5}
    USD_TO_CREDITS = 1000
    BALANCE_ON_CREATION = 500 

    
    user = models.ForeignKey(
        User,
        unique = True,
        null   = False)
    balance = models.IntegerField()
    
    def prepaid_product_ocr(self):
        return self.balance / Account.PRODUCT_CREDIT_CARGE['OCR']