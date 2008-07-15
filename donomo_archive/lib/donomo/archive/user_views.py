from __future__ import with_statement
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from docstore.utils.http import HttpResponseCreated
from docstore.core.models import Document, PageView, Query, Page, Binding
import docstore.core.utils  as core_utils
import docstore.utils.pdf as pdf_utils
import docstore.core.api  as core_api
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response
from django.conf import settings
from docstore import log

from xml.sax import saxutils
import urllib
import httplib2
from cStringIO import StringIO
import os

def upload_index(request):
    return HttpResponse('admin wants this for some reason...')

# ---------------------------------------------------------------------------

@http_method_dispatcher
def front_page():
    return { 'GET' : front_page__GET }

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def front_page__GET(request):
    """ Renders different templates if the user is logged in or not
    """
    if not request.user.is_authenticated():
        return render_to_response(
            'ui/front.html',
            { 'document_count' : Document.objects.count(),
              'page_count'     : Page.objects.count(),
              },
            context_instance = RequestContext(request))
    else:
        return render_to_response(
            'ui/home.html',
            { 'search_query' : request.GET.get('q','') },
            context_instance = RequestContext(request))

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def get_document_info(request, id):
    format = request.GET.get('format', 'application/json')
    viewtype = request.GET.get('viewtype', None)

    doc = Document.objects.get(id = id)

    if format == 'application/pdf':
        # Create the HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'filename=%s.pdf' % doc
        return pdf_utils.render_document(doc, response)

    if format == 'application/json':
        return render_to_response(
            "core/document.json",
            { "document" : doc, "viewtype" : viewtype},
            context_instance=RequestContext(request))

    if format == 'text/html':
        page_ids = list()
        bindings = Binding.objects.filter(document = doc)
        for b in bindings:
            page_ids.append(b.page.id)

        return render_to_response(
            "ui/search.html",
            { "document" : doc, "page_ids" : page_ids },
            context_instance=RequestContext(request))
    return HttpResponse('not supported GET for format %s' % format)

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def document_details__POST(request, id):

    """
    """

    page = Page.objects.get(id = request['page_id'])
    viewtype = request.POST.get('viewtype', None)
    doc = Document.objects.get(id = id)

    core_api.bind_page(doc, page)

    return render_to_response(
        "core/document.json",
        { "document" : doc, "viewtype" : viewtype },
        context_instance=RequestContext(request) )

# ---------------------------------------------------------------------------

def _get_ids_from_solr_response(content):
    from Ft.Xml.Domlette import NonvalidatingReader
    doc = NonvalidatingReader.parseString(content)
    dom_results = doc.xpath(u"//doc")

    logging.info(content)
    doc_ids = dict()
    for res in dom_results:
        log.debug(res)
        for n in res.childNodes:
            if n.localName is not None and n.localName == 'str':
                #log.debug("***" + str(n.attributes))
                name = n.attributes[(None,'name')].value
                if name == 'doc_id':
                    doc_id = str(n.firstChild.nodeValue)
                if name == 'page_id':
                    page_id = str(n.firstChild.nodeValue)

        page_ids = ids.get(doc_id, list())
        page_ids.append(page_id)
        doc_ids[doc_id] = page_ids

    log.debug(str(doc_ids))
    return doc_ids

@login_required()
def search(request):
    if request.method == 'GET':
        query_string = urllib.urlencode(
            {
                'q' : '%s AND owner:%d' % (request['q'], request.user.id),
                'version' : 2.2,
                'start'   : 0,
                'rows'    : 10,
                'indent'  : 'on',
                'hl'      : 'true',
                }
            )

        log.debug('search query is %s' % query_string)

        hc = httplib2.Http()

        request_url = 'http://%s/solr/select/?%s' % (settings.SOLR_HOST, query_string)
        res, content = hc.request(request_url, 'GET')
        log.debug('GET to %s returns %s\n%s' %(request_url, res, content))

        if res.status == 200:
            ids = _get_ids_from_solr_response(content)

            _create_query_log(request.user, request['q'], ids)

            return render_to_response("core/search_results.json",
                                      {"documents" : ids,
                                       "viewtype" : request["viewtype"],
                                       "search_query" : request['q']},
                                      context_instance=RequestContext(request))
        else:
            return HttpResponse('search server returned an error ' + str(res.status))

def _create_query_log(user, query_string, results):
    """returns a new event log based on a search string and results"""
    query = None
    if len(results) > 0:
        query = Query(owner = user,
                      name = query_string,
                      value = str(len(results)))
        query.save()

    return query

@login_required()
def doc_index(request):
    if request.method == 'GET':
        format = request.GET.get('format', 'application/json')

        if format == 'application/json':
            return render_to_response("core/documents.json", {
                                             "documents" : Document.objects.filter(owner = request.user).select_related(),
                                             "viewtype" : request.GET.get('viewtype', 'jpeg-original')
                                             },
                                             context_instance=RequestContext(request))
        return HttpResponse(str(Document.objects.count()))

    elif request.method == 'POST':
        document = Document.objects.create( owner = request.user, title = request['title'] )
        return HttpResponseCreated(document.get_absolute_url())
    else:
        return HttpResponseBadRequest()

@login_required()
def page_detail(request, page_id):
    """
    returns a page view given the format parameter.
    404 is returned if
        if a user attempts to retrieve a page that isn't his
        page id not found
    """
    try:
        page = Page.objects.get(id = page_id, owner = request.user)
    except Page.DoesNotExist, e:
        return HttpResponseNotFound("page %d not found for user %s" % (page_id, request.user))

    if request.method == 'GET':
        if request['format'] == 'application/pdf':
            # Create the HttpResponse object with the appropriate PDF headers.
            response = HttpResponse(mimetype='application/pdf')
            response['Content-Disposition'] = 'filename=%s.pdf' % page
            return pdf_utils.render_page(page, response)
        elif request['format'] == 'text/html':
            page_ids = list()
            page_ids.append(page.id)
            doc = Binding.objects.get(page = page).document
            return render_to_response("ui/search.html", {
                                     "document" : doc,
                                     "page_ids" : page_ids
                                     },
                                     context_instance=RequestContext(request))

        else:
            return HttpResonseBadRequest('unsupported format parameter.')
    elif request.method == 'DELETE':
        page.delete()
    else:
        return HttpResonseBadRequest('unsupported method %s' % request.method)

@login_required()
def tags(request):
    if not request.method.upper() == 'GET':
        return HttpResponseNotAllowed(['GET'])

    prefix = request.GET.get('startswith', None)

    if prefix:
        tag_set = request.user.tags.filter(istartswith=prefix.lower())
    else:
        tag_set = request.user.tags.all()

    return render_to_response(
        'core/tags.json',
        { 'tag_set' : tag_set },
        context_instance = RequestContext(request))

@login_required()
def doc_tags(request, doc_id):
    method = request.method.upper()
    allowed_methods = ( 'GET', 'PUT' )
    if method not in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)

    doc_list = Document.objects.filter( owner = request.user, id = doc_id )
    if len(doc_list) != 1:
        return HttpResponseNotFound('No document matching %s for %s' % (doc_id, request.user))

    document = doc_list[0]

    if method == 'GET':
        return render_to_response(
            'core/tags.json',
            { 'tag_set' : document.tag_set },
            context_instance = RequestContext(request))

    if method == 'PUT':
        if request.POST.has_key('tags'):
            tags = request.POST['tags']
        else:
            tags = ','.join(request.POST.getlist('tag'))
        document.tags = tags
        return HttpResponse()

