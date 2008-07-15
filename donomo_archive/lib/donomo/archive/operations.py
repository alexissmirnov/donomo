"""
The basic operations the can be performed on the document archive.  These
functions encapsulate all of the logic/management that goes into carrying
out these operations, including:

  - event logging
  - S3 uploads/downloads

"""

#
# pylint: disable-msg=C0103,W0142,W0212,W0401,W0614,W0702
#
#   C0103 - variables at module scope must be all caps
#   W0142 - use of * and ** magic
#   W0212 - access to protected class member (model._meta)
#   W0401 - wildcard import
#   W0614 - unused import from wildcard
#   W0702 - catch exceptions of unspecifed type
#

from __future__                         import with_statement
from django.contrib.contenttypes.models import ContentType
from django.core.validators             import ValidationError
from donomo.archive.models              import *
from donomo.archive.utils               import s3 as s3_utils
from donomo.archive.utils               import sqs as sqs_utils
from logging                            import getLogger
from platform                           import node
from socket                             import gethostbyname, gaierror
from django.db                          import connection

import mimetypes
import os
import tempfile

logging    = getLogger('donomo-archive')
page_meta  = manager(Page).model._meta
get_field  = page_meta.get_field
quote_name = connection.ops.quote_name
get_cursor = connection.cursor

# ---------------------------------------------------------------------------

def create_upload_from_stream(
    processor,
    owner,
    file_name,
    data_stream,
    content_type ):

    """
    Upload a new object into the archive.
    """

    upload = manager(Upload).create(
        owner     = owner,
        gateway   = processor,
        file_name = os.path.basename(file_name) )

    create_work_item(processor, upload, data_stream, content_type)

    return upload

# ---------------------------------------------------------------------------

def create_upload_from_file(
    processor,
    owner,
    file_name,
    content_type = None ):

    """
    Upload a new object into the archive.

    """

    with open(file_name, 'rb') as data_stream:
        return create_upload_from_stream(
            processor,
            owner,
            file_name,
            data_stream,
            content_type or guess_mime_type(file_name))

# ---------------------------------------------------------------------------

def create_document( owner, title = None):
    """
    Create a new document
    """

    # TODO: add document creation event history
    # TODO: add timestamp to end of document title

    document = manager(Document).create(
        title = title or 'New Document',
        owner = owner)

    return document

# ---------------------------------------------------------------------------

def create_page (document, position = None):
    """
    Create a new page
    """

    # TODO: add page creation event history

    page = manager(Page).create(
        document = document,
        owner    = document.owner,
        position = position or (document.num_pages + 1))

    return page

# ---------------------------------------------------------------------------

def split_document( document, at_page_number):
    """
    Split the given document into two documents, moving all pages starting
    from at_page_number and beyond into the new document.

    """

    # TODO: add page binding event

    if at_page_number < 1:
        raise Exception(
            'Cannot split document at position %d' % at_page_number)

    new_document = create_document(document.owner, 'New Document')
    cursor       = get_cursor()

    params = {
        'old_doc_id'      : document.id,
        'new_doc_id'      : new_document.id,
        'owner_id'        : document.owner.id,
        'offset'          : at_page_number,
        'page_table'      : quote_name(page_meta.db_table),
        'document_column' : quote_name(get_field('document').column),
        'owner_column'    : quote_name(get_field('owner').column),
        'position_column' : quote_name(get_field('position').column),
        }

    cursor.execute("""
        UPDATE    %(page_table)s
          SET     %(document_column)s = %(new_document_id)d,
                  %(position_column)s = %(position_column)s - %(offset)d
          WHERE   %(document_column)s = %(old_document_id)d
                  AND %(owner_column)s = %(owner_id)d
                  AND %(position_column)s > %(offset)d;""" % params)

    return new_document


# ---------------------------------------------------------------------------

def merge_documents( target, source, offset):
    """
    Append the source document to the end of the target, removing the source
    doucment upon completion

    """
    if target.owner != source.owner:
        raise Exception('Cannot merge documents owned by different users')

    if target == source:
        # avoid odd requests
        return

    if offset is None:
        offset = target.num_pages
    elif (offset < 0 or offset > target.num_pages):
        raise ValidationError('Invalid merge position: %d' % offset)

    cursor = get_cursor()

    params = {
        'src_doc_id'      : source.id,
        'tgt_doc_id'      : target.id,
        'owner_id'        : target.owner.id,
        'offset'          : offset or target.num_pages,
        'required_space'  : source.num_pages,
        'page_table'      : quote_name(page_meta.db_table),
        'document_column' : quote_name(get_field('document').column),
        'owner_column'    : quote_name(get_field('owner').column),
        'position_column' : quote_name(get_field('position').column),
        }

    #
    # Make space in the target document
    #

    if offset is not None:
        cursor.execute("""
          UPDATE    %(page_table)s
            SET     %(position_column)s = %(position_column)s + %(required_space)d
            WHERE   %(owner_column)s = %(owner_id)d
                    AND %(document_column)s = %(tgt_doc_id)d
                    AND %(position_column)s > %(offset)d;""" % params)

    #
    # insert the source doucment into the space
    #

    cursor.execute("""
        UPDATE    %(page_table)s
          SET     %(document_column)s = %(tgt_doc_id)d,
                  %(position_column)s = %(position_column)s + %(offset)d
          WHERE   %(document_column)s = %(src_doc_id)d
                  AND %(owner_column)s = %(owner_id)d;""" % params)

    #
    # Delete the source document
    #

    source.delete()

    #
    # TODO: add page binding event
    #


# ---------------------------------------------------------------------------

def move_page(
    source_document,
    source_offset,
    target_document,
    target_offset ):

    """
    Move a page from one document/position to another.

    """


    cursor = get_cursor()

    params = {
        'owner_id'        : target_document.owner.pk,
        'src_doc_id'      : source_document.pk,
        'tgt_doc_id'      : target_document.pk,
        'src_offset'      : source_offset,
        'tgt_offset'      : target_offset,
        'page_table'      : quote_name(page_meta.db_table),
        'document_column' : quote_name(get_field('document').column),
        'owner_column'    : quote_name(get_field('owner').column),
        'position_column' : quote_name(get_field('position').column),
        }

    #
    # Make space in the target document
    #

    cursor.execute("""
        UPDATE    %(page_table)s
          SET     %(position_column)s = %(position_column)s + 1
          WHERE   %(owner_column)s = %(owner_id)d
                    AND %(document_column)s = %(tgt_doc_id)d
                    AND %(position_column)s > %(tgt_offset)d;""" % params)

    #
    # Move source page into target document
    #

    cursor.execute("""
        UPDATE    %(page_table)s
          SET     %(document_column)s = %(tgt_doc_id)d,
                  %(position_column)s = %(tgt_offset)d
          WHERE   %(document_column)s = %(src_doc_id)d
                    AND %(owner_column)s = %(owner_id)d
                    AND %(position_column)s = %(src_offset)d;""" % params)

    #
    # Close gap in the source document
    #
    cursor.execute("""
        UPDATE    %(page_table)s
          SET     %(position_column)s = %(position_column)s - 1
          WHERE   %(owner_column)s = %(owner_id)d
                    AND %(document_column)s = %(src_doc_id)d
                    AND %(position_column)s > %(src_offset)d;""" % params)

    # TODO: add evcent to history

#-----------------------------------------------------------------------------

def get_or_create_processor(
    name,
    default_outputs ):

    """
    Obtain a processor object based on its name and the names of its
    outputs.  The processor will be created if it does not already
    exist.  On creating a processessor, this function assumes it will
    be running on local node.

    """

    process, created = manager(Process).get_or_create(
        name = name)

    if created:
        logging.info('Registered process: %s' % process)

    if process.outputs.count() == 0:
        logging.info('Adding default output routing for %s' % process)
        for view_name, consumers in default_outputs:
            view_type = manager(ViewType).get_or_create(name = view_name)[0]
            view_type.producers.add(process)
            for consumer in consumers:
                consumer = manager(Process).get_or_create(name = consumer) [0]
                view_type.consumers.add(consumer)

    try:
        address = gethostbyname(node())
    except gaierror:
        address = '127.0.0.1'
        logging.exception(
            'Failed to retrieve local address; using %s' % address)


    processor, created = manager(Processor).get_or_create(
        process = process,
        node    = manager(Node).get_or_create(
            address = address )  [ 0 ] )

    if created:
        logging.info('Registered processor: %s' % processor)

    sqs_utils.create_queue(processor.queue_name)

    logging.debug('Retrieved processor: %s' % processor)

    return processor

#-----------------------------------------------------------------------------

def create_page_view_from_stream(
    processor,
    output_channel,
    page,
    data_stream,
    content_type ):

    """
    Create a page view work item on the output channel (given by
    name) from the passed data stream.

    """
    view_type = processor.output.get( name = output_channel )

    page_view = manager(PageView).get_or_create(
        page      = page,
        view_type = view_type ) [0]

    create_work_item(
        processor,
        page_view,
        data_stream,
        content_type)

#-----------------------------------------------------------------------------

def create_page_view_from_file(
    processor,
    output_channel,
    page,
    file_name,
    content_type = None):

    """
    Create a page view work item on the output channel (given by
    name) from the contents of the file denoted by path.

    """

    with open(file_name, 'rb') as data_stream:
        create_page_view_from_stream(
            processor,
            output_channel,
            page,
            data_stream,
            content_type or guess_mime_type(file_name))

#-----------------------------------------------------------------------------

def create_work_item(
    processor,
    work_item,
    data_stream,
    content_type ):

    """
    Upload a file to S3 then broadcast a message to one or more SQS
    queues.

    work_item:
        Data model object representing a work item - a page view or
        an upload.

    data_stream:
        The actual data that corresponds to this work item. will be
        saved in s3

    content_type:
        Content type of the data comprising work item

    """

    view_type = work_item.view_type
    meta_data = ContentType.objects.get_for_model(work_item)
    s3_key   = work_item.s3_key
    item_type = '%s.%s' % (meta_data.app_label, meta_data.model)

    logging.info(
        'Creating work item: ' \
            'processor = %s, ' \
            'view_type = %s, ' \
            'item_type = %s, ' \
            'item_id = %s' % (
            processor,
            view_type,
            item_type,
            work_item.id ))

    s3_utils.upload_stream(
        s3_utils.get_bucket(),
        s3_key,
        data_stream,
        content_type )

    message = {
        'Content-Type' : content_type,
        'S3-Key'       : s3_key,
        'Model-Name'   : item_type,
        'Primary-Key'  : work_item.id,
        }

    sqs_connection = sqs_utils.get_connection()

    for next_processor in view_type.consumers.all():
        logging.info('Notifying %s' % next_processor)
        sqs_utils.post_message(
            sqs_utils.create_queue(
                next_processor.queue_name,
                sqs_connection),
            message )

#-----------------------------------------------------------------------------

def get_work_item(
    processor,
    max_wait_time  = None,
    interrupt_func = None,
    poll_frequency = None ):

    """
    Retrieve the next work item for the given processor

    """
    temp_path = None

    try:
        sqs_queue = sqs_utils.get_queue(processor.queue_name)

        message = sqs_utils.get_message(
            sqs_queue          = sqs_queue,
            visibility_timeout = processor.visibility_timeout,
            max_wait_time      = max_wait_time,
            interrupt_func     = interrupt_func,
            poll_frequency     = poll_frequency )

        if message is None:
            return None

        logging.debug(
            'Retrieved message %s from queue %s' % (
                message,
                processor.queue_name ))

        message_content_type = message['Content-Type']

        temp_fd, temp_path = tempfile.mkstemp(
            mimetypes.guess_extension(message_content_type) or '.bin',
            '%s-work-item-' % processor.name,
            processor.temp_dir )

        logging.debug('Downloading work item to %s' % temp_path)

        message_s3_path = message['S3-Key']

        with os.fdopen(temp_fd,'wb') as file_stream:
            metadata = s3_utils.download_stream(
                s3_utils.get_bucket(),
                message_s3_path,
                file_stream )

        logging.debug('Created work item file at %s' % temp_path)

        model = django.db.models.get_model(*message['Model-Name'].split('.'))
        instance = model.objects.get(id = int(message['Primary-Key']))

        assert( message_s3_path == instance.s3_path )
        assert( message_content_type == metadata['Content-Type'] )

        message.update( metadata )

        message.update(
            { 'Local-Path'     : temp_path,
              'Model'          : model,
              'Object'         : instance,
              'Processor'      : processor,
              })

        logging.info(
            'Retrieved work item: ' \
                'processor = %(Processor)s,'
                'model = %(Model)s, ' \
                'object = %(Object)s, ' \
                'content-type = %(Content-Type)s' % message)

        return message

    except:
        logging.exception("%s - failed to retrieve work item" % processor)
        if temp_path:
            os.remove(temp_path)
        return None

#-----------------------------------------------------------------------------

def close_work_item(processor, message, delete_from_queue):

    """
    Finish handling the given work_item, deleting it from the input
    queue if delete_from_queue is true

    """

    logging.info("%s : closing work item %s" % (processor, message))

    if delete_from_queue:
        logging.info("Removing %s from message_queue" % message)
        sqs_utils.delete_message(message)

    local_path = message['Local-Path']
    if os.path.exists(local_path):
        logging.debug('Deleting local copy from %s' % local_path)
        os.remove(local_path)

#-----------------------------------------------------------------------------

