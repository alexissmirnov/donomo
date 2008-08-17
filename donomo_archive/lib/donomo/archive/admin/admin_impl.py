"""
Admin function implementations
"""

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from donomo.archive.utils import sqs as sqs_utils
from donomo.archive.utils import s3 as s3_utils
from donomo.archive.models import manager, Document, Page, Upload
from donomo.archive.service import indexer
import logging

logging = logging.getLogger('admin')

###############################################################################

@staff_member_required
def get_queue_list(request):
    """
    Get the list of queues used by the archive
    """
    logging.warn('Retrieving queue list for %s' % request.user)

    sqs_conn   = sqs_utils.get_connection()
    all_queues = sqs_conn.get_all_queues()

    return render_to_response('archive_admin/queues.html', {'queues' : all_queues } )

###############################################################################

@staff_member_required
def delete_all_queues(request):
    """
    Wipe all queues used by the archive.
    """
    # TODO: delete_all_queues really shouldn't be exposed!
    logging.warn('%s requesting delete of all queues' % request.user)
    for queue in sqs_utils.get_connection().get_all_queues():
        queue.clear()
        queue.delete()
    return HttpResponse('OK')

###############################################################################
@staff_member_required
def get_queue_info(request, queue_name):
    """
    Get queue information
    """
    logging.warn(
        '%s requesting queue details for %s' % (
            request.user,
            queue_name ))
    queue = sqs_utils.get_connection().create_queue(queue_name)
    return HttpResponse(
        '%s has %s messages' % (queue.id, queue.count()))
###############################################################################
###############################################################################
@staff_member_required
def delete_queue(request, queue_name):
    """
    Erase a queue.
    """
    logging.warn(
        '%s requesting delete of %s' % (
            request.user,
            queue_name))
    queue = sqs_utils.get_queue(queue_name)
    count = queue.count()
    queue.clear()
    queue.delete()
    return HttpResponse(
        'Queue %s with %s messages was deleted' % (
            queue_name,
            count ))

###############################################################################

@staff_member_required
def get_status(request):
    """
    Get a quick status of the archive
    """
    return HttpResponse('%s documents' % manager(Document).count())

###############################################################################
@staff_member_required
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
    delete_bucket_contents()
    return HttpResponse('everything deleted')


###############################################################################

@staff_member_required
def reset_search_index(request = None):
    """
    Reset the search index.
    """
    # TODO: implement reset_search_index
    return HttpResponse('Not implemented', status=500)


###############################################################################

@staff_member_required
def delete_search_index( request = None ):
    """
    Documentation goes here

    """
    try:
        indexer.reset()
        return HttpResponse(
            content = 'search index deleted',
            content_type = 'text/plain' )
    except Exception, e:
        return HttpResponse(
            status       = 500,
            content      = str(e),
            content_type = 'text/plain' )

###############################################################################

def delete_bucket_contents():
    """
    Documentation goes here

    """
    for key in s3_utils.get_bucket().get_all_keys():
        key.delete()
