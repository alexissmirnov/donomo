from django.http                            import HttpResponse, HttpResponseRedirect
from donomo.archive.utils.http              import HttpResponsePaymentRequired
from django.contrib.auth.decorators  import login_required

@login_required
def expense(request):
    account = Account.get(user = request.user)
    balance = account.balance - request.REQUEST['charge']
    
    if balance > 0:
        account.balance = balance
        account.save()
        return HttpResponse()
    else:
        return HttpResponsePaymentRequired("{'error': 'balance low'}")