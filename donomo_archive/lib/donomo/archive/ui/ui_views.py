from donomo.archive.models import Document, Page, manager
from django.template import RequestContext
from django.shortcuts import render_to_response

# ---------------------------------------------------------------------------

def front_page(request):
    """ Renders different templates if the user is logged in or not
    """
    if not request.user.is_authenticated():
        return render_to_response(
            'ui/front.html',
            { 'document_count' : manager(Document).count(),
              'page_count'     : manager(Page).count(),
              },
            context_instance = RequestContext(request))
    else:
        return render_to_response(
            'ui/home.html',
            { 'search_query' : request.GET.get('q','') },
            context_instance = RequestContext(request))

# ---------------------------------------------------------------------------
