"""
The basic operations the can be performed on the document archive.  These
functions encapsulate all of the logic/management that goes into carrying
out these operations, including:

  - event logging
  - S3 uploads/downloads

"""

#
# pylint: disable-msg=C0103,R0913,W0142,W0212,W0401,W0614,W0702
#
#   C0103 - variables at module scope must be all caps
#   R0913 - too many arguments to function
#   W0142 - use of * and ** magic
#   W0212 - access to protected class member (model._meta)
#   W0401 - wildcard import
#   W0614 - unused import from wildcard
#   W0702 - catch exceptions of unspecifed type
#

from __future__                         import with_statement
from django.core.validators             import ValidationError
from django.conf                        import settings
from donomo.archive.models              import *
from donomo.archive.utils               import s3, sqs, misc
from platform                           import node
from socket                             import gethostbyname, gaierror
from cStringIO                          import StringIO

import django.db
import mimetypes
import os
import tempfile
import shutil
import logging
from time import gmtime, strftime

logging    = logging.getLogger('donomo-archive')
page_meta  = manager(Page).model._meta
get_field  = page_meta.get_field
quote_name = django.db.connection.ops.quote_name
get_cursor = django.db.connection.cursor

#
# If you add a publicly visible operation to this module, don't forget to
# add it's name to __all__.
#

__all__ = (
    'create_document',
    'create_page',
    'split_document',
    'merge_documents',
    'move_page',
    'create_asset_from_stream',
    'create_asset_from_file',
    'publish_work_item',
    'retrieve_work_item',
    'close_work_item',
    )

###############################################################################

def create_document( processor, owner, title = None):
    """
    Create a new document
    """

    if title is None:
        title = 'Created on %s' % strftime(
            "%Y-%m-%d %Y %H:%M:%S",
            gmtime())

    logging.info( 'Creating new document for %s: %s' % ( owner, title))

    document = manager(Document).create( title = title, owner = owner)

    asset = create_asset_from_stream(
        data_stream = StringIO(''),
        owner = owner,
        producer = processor,
        asset_class = AssetClass.DOCUMENT,
        related_document = document,
        child_number = 1,
        mime_type = MimeType.BINARY )

    return (document, asset)

###############################################################################

def create_page (document, position = None):
    """
    Create a new page
    """

    page = manager(Page).create(
        document = document,
        owner    = document.owner,
        position = position or (document.num_pages + 1))

    return page

###############################################################################

def split_document( document, offset ):

    """ Split the given document into two documents, moving all pages
        after offset into the new document.  For example, splitting a
        10 page document at offset 5 results in pages 1 through 5
        staying in the original document and pages 6 through 10 moving
        into the new document.

    """

    if offset < 1:
        raise Exception(
            'Cannot split document at position %d' % offset)

    new_document = create_document(document.owner,
                                   document.title +
                                   '/1(%d-%d)' %
                                   (offset + 1, document.num_pages))

    for page in document.pages.filter( position__gt=offset ):
        page.document =  new_document
        page.position -= offset
        page.save()

    document.title = document.title + '/2(0-%d)' % offset
    document.save()

    return new_document


###############################################################################

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

    target_length = target.num_pages

    if offset is None:
        offset = target_length
    elif (offset < 0 or offset > target_length):
        raise ValidationError('Invalid merge position: %d' % offset)

    #
    # Make space in the target document
    #

    source_length = source.num_pages

    for page in target.pages.filter( position__gt=offset ):
        page.position += source_length
        page.save()

    #
    # insert the source document into the space
    #

    for page in source.pages.all():
        page.document =  target
        page.position += offset
        page.save()

    #
    if target.title.split('/')[0] == source.title.split('/')[0]:
        target.title = target.title.split('/')[0]
    else:
        target.title = target.title + ':' + source.title
    target.save()

    #
    # Delete the source document
    #

    source.delete()


###############################################################################

def initialize_infrastructure():
    """  Initialize the AWS infrastructure used by donomo archive.
    """

    s3.initialize()
    sqs.initialize()

###############################################################################

def initialize_processor(
    name,
    default_inputs = None,
    default_outputs = None,
    default_accepted_mime_types = None ):

    """ Obtain a processor object based on its name and the names of its
        outputs.  The processor will be created if it does not already
        exist.  On creating a processor, this function assumes it will
        be running on local node.

        Returns a tuple processor and a boolean indicating if the
        processor was created.

    """

    process, created = manager(Process).get_or_create( name = name )

    if created:
        logging.debug('Registered process: %s' % process)

        logging.debug('Setting up input routing for %s' % process)

        for value in default_inputs or ():
            process.inputs.add(
                manager(AssetClass).get_or_create( name = value ) [0] )

        for value in default_outputs or ():
            process.outputs.add(
                manager(AssetClass).get_or_create( name = value ) [0] )

        for value in default_accepted_mime_types or ():
            extension = misc.guess_extension(value)
            process.mime_types.add(
                manager(MimeType).get_or_create(
                    name = value,
                    defaults = { 'extension' : extension }) [0] )

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
        logging.debug('Registered processor: %s' % processor)

    logging.debug('Retrieved processor: %s' % processor)

    return processor, created

###############################################################################

def upload_asset_stream( asset, data_stream ):

    """ Upload an asset stream to S3

    """

    logging.info('Uploading %r' % asset)

    s3.upload_from_stream( asset.s3_key, data_stream, asset.mime_type.name )

###############################################################################

def upload_asset_file( asset, file_name ):

    """ Upload an asset file to S3

    """

    with open(file_name, 'rb') as data_stream:
        upload_asset_stream(asset, data_stream)

###############################################################################

def create_asset_from_stream( data_stream, **kwargs ):

    """ Create a page view work item on the output channel (given by name)
        from the passed data stream.

    """
    logging.debug(
        'Creating Asset<%s>' % ', '.join(
            '%s=%s' % n_v for n_v in kwargs.iteritems() ) )

    asset = manager(Asset).create(**kwargs)

    return asset

###############################################################################

def create_asset_from_file( file_name, **kwargs ):

    """ Create a page view work item on the output channel (given by name)
        from the contents of the file denoted by path.

    """

    kwargs = kwargs.copy()
    kwargs.setdefault('orig_file_name', file_name)
    kwargs.setdefault('mime_type', misc.guess_mime_type(file_name))

    with open(file_name, 'rb') as data_stream:
        return create_asset_from_stream( data_stream, **kwargs )

###############################################################################

def _enqueue_work_item( is_new, asset_list ):

    """ Broadcast messages about the existence or modification of an set
        of assets to the relevant listening services.

    """

    logging.info(
        '%sueuing work items:%s' % (
            is_new and 'Q' or 'Re-q',
            ''.join( '\n  %r' % a for a in asset_list )))

    sqs.post_message_list(
        ( {  'Asset-ID'     : asset.pk,
             'Process-Name' : consumer.name,
             'Is-New'       : is_new and 1 or 0 }
          for asset in asset_list
          for consumer in asset.consumers ) )

###############################################################################

def publish_work_item( *asset_list ):

    """ Inform the processing pipeline about newly added assets.

    """

    _enqueue_work_item( True, asset_list )

###############################################################################

def reprocess_work_item( *asset_list ):

    """ Ask the processing pipeline to re-process existing assets.

    """

    _enqueue_work_item( False, asset_list )


###############################################################################

def instantiate_asset( asset_id):

    """ Lookup the asset referenced by the message and instantiate a local
        copy of it.
    """

    temp_dir = tempfile.mkdtemp(
        prefix = 'donomo-work-item-',
        dir    = settings.TEMP_DIR )

    try:
        asset = manager(Asset).get( pk = asset_id )

        meta_data = {
            'Asset-Instance' : asset,
            'Asset-Class'    : asset.asset_class,
            'Owner'          : asset.owner,
            }

        meta_data.update(
            s3.download_to_file(
                s3_source_path  = asset.s3_key,
                local_dest_path = os.path.join(temp_dir, asset.file_name)))

        logging.info( 'Instantiated %r' % asset )

        return meta_data

    except:
        logging.exception(
            "Failed to retrieve work item: %(Asset-ID)s" % message)
        shutil.rmtree(temp_dir)
        raise

###############################################################################

def retrieve_work_item(
    visibility_timeout = 300,
    max_wait_time      = None,
    interrupt_func     = None,
    auto_get_asset     = True ):

    """ Retrieve the next work item from the queue.

    """

    try:

        message = sqs.get_message(
            visibility_timeout = visibility_timeout,
            max_wait_time      = max_wait_time,
            interrupt_func     = interrupt_func )

        if message and auto_get_asset:
            message.update(instantiate_asset(message['Asset-ID']))

        return message

    except:
        return None

###############################################################################

def close_work_item(work_item, delete_from_queue):

    """
    Finish handling the given work_item, deleting it from the input
    queue if delete_from_queue is true

    """

    logging.info(
        "%s asset %s" % (
            (delete_from_queue and 'closing' or 'aborting'),
            work_item['Asset-ID'] ))

    local_path = work_item.get('Local-Path')

    if delete_from_queue:
        sqs.delete_message(work_item)

    if local_path and os.path.exists(local_path):
        shutil.rmtree(os.path.dirname(local_path))

###############################################################################

