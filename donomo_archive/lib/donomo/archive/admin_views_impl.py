from __future__ import with_statement
from docstore.utils.http import HttpResponseCreated
from docstore.core.models import Document, PageView, Query, Page, Binding
import docstore.core.utils  as core_utils
import docstore.utils.pdf as pdf_utils
import docstore.core.api  as core_api
from django.template import RequestContext
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.conf import settings
from docstore import log

from xml.sax import saxutils
import urllib
import httplib2
from cStringIO import StringIO
import os


from django.http import HttpResponse
from donomo.archive.utils import sqs as sqs_utils
from donomo.archive.utils import s3 as s3_utils


# ----------------------------------------------------------------------------

@staff_member_required
def upload_index(request):
    """
    What is this supposed to be?
    """
    return HttpResponse('admin wants this for some reason...')


# ----------------------------------------------------------------------------

@staff_member_required
def get_queue_list(request):
    """
    Get the list of queues used by the archive

    """
    sqs_conn   = sqs_utils.get_connection()
    all_queues = sqs_conn.get_all_queues()

    return HttpResponse(
        '%s queues:\n%s' % (
            len(all_queues),
            ', '.join( [queue.id for queue in all_queues ])))

# ----------------------------------------------------------------------------

@staff_member_required
def delete_all_queues(request):
    """
    Wipe all queues used by the archive.
    """
    # TODO: delete_all_queues really shouldn't be exposed!
    for queue in sqs_utils.get_connection().get_all_queues():
        queue.clear()
        queue.delete()
    return HttpResponse('OK')

# ----------------------------------------------------------------------------

@staff_member_required
def get_queue_detail(request, queue_name):
    queue = sqs_utils.get_connection().create_queue(queue_name)
    return HttpResponse(
        '%s has %d messages' % (queue.id, queue.count()))

# ----------------------------------------------------------------------------

@staff_member_required
def delete_queue(request, queue_name):
    queue = sqs_conn.get_queue(queue_name)
    count = queue.count()
    queue.clear()
    queue.delete()
    return HttpResponse(
        'Queue %s with %d messages was deleted' % (
            queue_name,
            count ))

# ----------------------------------------------------------------------------

@staff_member_required
def get_status(request):
    """
    Get a quick status of the archive
    """
    return HttpResponse('%s documents' % manager(Document).count())

# ----------------------------------------------------------------------------

def wipe_everything(request):
    """
    Delete everything and start over
    """
    # TODO: wipe_everything ... are we INSANE!!!
    manager(Upload).all().delete()
    manager(Document).all().delete()
    manager(Page).all().delete()
    delete_all_queues(None)
    delete_search_index()
    delete_bucket_contents(bucket)
    return HttpResponse('everything deleted')


# ----------------------------------------------------------------------------

@staff_member_required
def search_index(request):
    if request.method == 'DELETE':
        delete_search_index()
    elif request.method == 'POST':
        for doc in Documents.objects.all():
            key = Key(bucket)
            key.key = '%s/ocr.txt' % id
            ocr = key.get_contents_to_string()
            from docstore.processors.search_index import index_string
            index_string(id, ocr)
    else:
        return HttpResponse('GET does nothing')

# ----------------------------------------------------------------------------

@staff_member_required
def delete_search_index( request = None ):
    try:
        indexer.reset()
        return HttpResponse(
            content = 'search index deleted',
            content_type = 'text/plain'
    except Exception, e:
        return HttpResponse(
            status       = 500,
            content      = str(e),
            content_type = 'text/plain')

# ----------------------------------------------------------------------------

@staff_member_required
def delete_bucket_contents(bucket):
    keys = bucket.get_all_keys()
    for key in keys:
        bucket.delete_key(key)
