from __future__ import with_statement
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from docstore.utils.http import HttpResponseCreated
from docstore.core.models import Document, PageView, Query, Page, Binding
import docstore.core.utils  as core_utils
import docstore.utils.pdf as pdf_utils
import docstore.core.api  as core_api
from django.template import RequestContext

from django.shortcuts import render_to_response
from django.conf import settings
from docstore import log

from xml.sax import saxutils
import urllib
import httplib2
from cStringIO import StringIO
import os
from django.contrib.auth.models import User

def upload_index(request):
    return HttpResponse('admin wants this for some reason...')

def index(request):
    """renders different templates if the user is logged in or not"""
    if not request.user.is_authenticated():
        return render_to_response('ui/front.html',
                                  {
                                    'document_count' : Document.objects.count()
                                  },
                                context_instance=RequestContext(request))
    else:
        print  'queries: ' + str(Query.objects.filter(owner = request.user))
        return render_to_response(
            'ui/home.html',
            {
              'document_count' : Document.objects.filter(
                                        owner = request.user).count(),
              'recent_queries' : Query.objects.filter(owner = request.user)
            },
            context_instance=RequestContext(request))

def doc_detail(request, id):
    if request.method == 'GET':
        format = request.GET.get('format', 'application/json')
        viewtype = request.GET.get('viewtype', None)
        
        doc = Document.objects.get(id = id)
        
        if format == 'application/pdf':
            # Create the HttpResponse object with the appropriate PDF headers.
            response = HttpResponse(mimetype='application/pdf')
            response['Content-Disposition'] = 'filename=%s.pdf' % doc
            return pdf_utils.render_document(doc, response)
        elif format == 'application/json':
            return render_to_response("core/document.json", {
                                             "document" : doc,
                                             "viewtype" : viewtype
                                             },
                                        context_instance=RequestContext(request))
        else:
            return HttpResponse('not supported GET for format %s' % format)
    elif request.method == 'POST':
        page = Page.objects.get(id = request['page_id'])
        viewtype = request.POST.get('viewtype', None)
        doc = Document.objects.get(id = id)
        
        core_api.bind_page(doc, page)
            
        return render_to_response("core/document.json", 
                                  {"document" : doc, "viewtype" : viewtype},
                                  context_instance=RequestContext(request))
    else:
        return HttpResponseBadRequest('only GET is supported')

def cache_image(page_id):
    try:
        page_view = PageView.objects.get(view_type__name = 'jpeg-original', page__id = page_id)
    except PageView.DoesNotExist, e:
        log.error('view type JPEG doesnt exist for page %s' % page_id)
        return

    page_view_image_path = os.path.join(settings.MEDIA_ROOT,str(page_id)+'.jpg')
    if not os.path.exists(page_view_image_path):
        with open(page_view_image_path,'wb') as file_stream:
            metadata = core_utils.download_file_from_s3(
                core_utils.get_s3_bucket(),
                page_view.s3_path,
                file_stream )

def search(request):
    if not request.user.is_authenticated():
        return HttpResponse('only logged in users can search')

    if request.method == 'GET':
        query_string = urllib.urlencode(
            {
                'q' : '%s AND owner:%d' % (request['q'], request.user.id),
                'version' : 2.2,
                'start'   : 0,
                'rows'    : 10,
                'indent'  : 'on',
                'hl'      : 'true',
                #'hl.fl'   : 'text',
                #'hl.fragsize' : 30,
                }
            )

        log.debug('search query is %s' % query_string)

        hc = httplib2.Http()

        request_url = 'http://%s/solr/select/?%s' % (settings.SOLR_HOST, query_string)
        res, content = hc.request(request_url, 'GET')
        log.debug('GET to %s returns %s\n%s' %(request_url, res, content))
        if res.status == 200:
            from xml.dom.ext.reader import PyExpat
            from xml.xpath import Evaluate

            reader = PyExpat.Reader()
            dom = reader.fromString(content)
            dom_results = Evaluate("//str[@name='id']", dom.documentElement)
            results = list()
            for res in dom_results:
                results.append(res.childNodes[0].nodeValue)
                
            _create_query_log(request.user, request['q'], results)

            return render_to_response("ui/search.html",
                                      {"page_ids" : results,
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

def queue_index(request):
    if request.method == 'GET':
        res = str(len(sqs_conn.get_all_queues())) + ' queues:\n'
        for q in sqs_conn.get_all_queues():
            res += q.id + ', '
        return HttpResponse(res)
    elif request.method == 'DELETE':
        for q in sqs_conn.get_all_queues():
            q.clear()
            sqs_conn.delete_queue(q)

def queue_detail(request, queue_name):
    if request.method == 'GET':
        queue = sqs_conn.create_queue(queue_name)
        #messages = queue.get_messages(100)

        res = queue.count() + ' messages in ' + queue.id
        #for m in messages:
        #    res += str(m.get_body()) + ', '
        return HttpResponse(res)

    elif request.method == 'DELETE':
        queue = sqs_conn.create_queue(queue_name)
        count = queue.count()
        queue.clear()
        sqs_conn.delete_queue(queue)
        return HttpResponse('queue ' + queue_name + ' with ' + count + ' messages was deleted')


def status(request):
    if request.method == 'DELETE':
        queue_index(request)
        Document.objects.all().delete()
        delete_search_index()
        delete_bucket_contents(bucket)
        return HttpResponse('everything deleted')
    elif request.method == 'GET':
        return HttpResponse('%s documents' % Document.objects.count())

def search_index(request):
    if request.method == 'DELETE':
        delete_search_index()
        return HttpResponse('search index deleted')
    elif request.method == 'POST':
        for doc in Documents.objects.all():
            key = Key(bucket)
            key.key = '%s/ocr.txt' % id
            ocr = key.get_contents_to_string()
            from docstore.processors.search_index import index_string
            index_string(id, ocr)
    else:
        return HttpResponse('GET does nothing')

def delete_search_index():
        solr_url = 'http://%s/solr/update' % settings.SOLR_HOST
        http_client = httplib2.Http()
        commit_resp, content = http_client.request(solr_url,
                'POST',
                body="<delete><query>*:*</query></delete><commit/>",
                headers={"Content-type":"text/xml; charset=utf-8"})

def delete_bucket_contents(bucket):
    keys = bucket.get_all_keys()
    for key in keys:
        bucket.delete_key(key)


def page_detail(request, page_id):
    """
    returns a page view given the format paramater.
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
    
        else:
            return HttpResonseBadRequest('unsupported format parameter.')
    elif request.method == 'DELETE':
        page.delete()
    else:
        return HttpResonseBadRequest('unsupported method %s' % request.method)