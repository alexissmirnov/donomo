"""
Admin function implementations
"""

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from donomo.archive.utils import sqs, s3
from donomo.archive.models import *
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

    return render_to_response(
        'archive_admin/queues.html', {'queues' : [ sqs._get_queue() ] } )

###############################################################################

@staff_member_required
def delete_all_queues(request = None):
    """
    Wipe all queues used by the archive.
    """
    # TODO: delete_all_queues really shouldn't be exposed!
    logging.critical('Delete of all queues' % request.user)
    for queue in [ sqs._get_queue() ]:
        if queue is not None:
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

    queue = sqs._get_connection().get_queue(queue_name)

    return HttpResponse(
        '%s has %s messages' % (queue.id, queue.count()))

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
    queue = sqs._get_queue(queue_name)
    count = queue.count()
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
    manager(Asset).all().delete()
    manager(Page).all().delete()
    manager(Document).all().delete()
    manager(Tag).all().delete()
    manager(User).exclude(is_staff=True).exclude(is_superuser=True).delete()

    delete_all_queues(request)
    delete_search_index()
    delete_bucket_contents()
    return HttpResponse('everything deleted')


###############################################################################
def delete_search_index():
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
    for key in s3._get_bucket().get_all_keys():
        key.delete()
