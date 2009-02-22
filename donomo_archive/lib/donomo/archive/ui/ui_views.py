from donomo.archive.models import Document, Page, manager
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators  import login_required

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
@login_required
def download_tags(request):
    """Download processed batch. Landing page.
    """
    return render_to_response('ui/download.html',
                              {'batch' : request.GET.get('batch','')},
                              context_instance = RequestContext(request))
