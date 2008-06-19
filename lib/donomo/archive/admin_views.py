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
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.conf import settings
from docstore import log

from xml.sax import saxutils
import urllib
import httplib2
from cStringIO import StringIO
import os

@staff_member_required
def upload_index(request):
    return HttpResponse('admin wants this for some reason...')


@staff_member_required
def queue_list(request):
    allowed_methods = ('GET', 'DELETE')

    if method not in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)

    sqs_conn   = core_utils.new_sqs_connection()
    all_queues = sqs_conn.get_all_queues()
    if request.method == 'GET':

        return HttpResponse(
            '%s queues:\n%s' % (
                len(all_queues),
                ', '.join( [queue.id for queue in all_queues ])))
    elif request.method == 'DELETE':
        for queue in all_queues:
            queue.clear()
            sqs_conn.delete_queue(queue)
        return HttpResponse('OK')

@staff_member_required
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

@staff_member_required
def status(request):
    if request.method == 'DELETE':
        queue_index(request)
        Document.objects.all().delete()
        delete_search_index()
        delete_bucket_contents(bucket)
        return HttpResponse('everything deleted')
    elif request.method == 'GET':
        return HttpResponse('%s documents' % Document.objects.count())

@staff_member_required
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

@staff_member_required
def delete_search_index():
    solr_url = 'http://%s/solr/update' % settings.SOLR_HOST
    http_client = httplib2.Http()
    commit_resp, content = http_client.request(
        solr_url,
        'POST',
        body="<delete><query>*:*</query></delete><commit/>",
        headers={"Content-type":"text/xml; charset=utf-8"})

@staff_member_required
def delete_bucket_contents(bucket):
    keys = bucket.get_all_keys()
    for key in keys:
        bucket.delete_key(key)
