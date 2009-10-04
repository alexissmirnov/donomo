from django.http                            import HttpResponse, HttpResponseRedirect
from donomo.archive.utils.http              import HttpResponsePaymentRequired
from django.contrib.auth.decorators  import login_required
import donomo.billing.models


@login_required
def expense(request):
    done = donomo.billing.models.charge(request.user, request.REQUEST['charge'])
    
    if done:
        return HttpResponse()
    else:
        return HttpResponsePaymentRequired("{'error': 'balance low'}")
