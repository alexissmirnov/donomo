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

import django.db
import mimetypes
import os
import tempfile
import shutil
import logging

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

def create_document( owner, title = None):
    """
    Create a new document
    """

    if title is None:
        title = 'New Document'

    logging.info( 'Creating new document for %s: %s' % ( owner, title))

    return manager(Document).create( title = title, owner = owner)

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

def split_document( document, at_page_number):
    """
    Split the given document into two documents, moving all pages starting
    from at_page_number and beyond into the new document.

    """

    if at_page_number < 1:
        raise Exception(
            'Cannot split document at position %d' % at_page_number)

    new_document = create_document(document.owner, 'New Document')
    cursor       = get_cursor()

    params = {
        'old_document_id' : document.pk,
        'new_document_id' : new_document.pk,
        'owner_id'        : document.owner.pk,
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

    num_target_pages = target.num_pages

    if offset is None:
        offset = num_target_pages
    elif (offset < 0 or offset > num_target_pages):
        raise ValidationError('Invalid merge position: %d' % offset)

    cursor = get_cursor()

    params = {
        'src_doc_id'      : source.pk,
        'tgt_doc_id'      : target.pk,
        'owner_id'        : target.owner.pk,
        'offset'          : offset,
        'required_space'  : source.num_pages,
        'page_table'      : quote_name(page_meta.db_table),
        'document_column' : quote_name(get_field('document').column),
        'owner_column'    : quote_name(get_field('owner').column),
        'position_column' : quote_name(get_field('position').column),
        }

    #
    # Make space in the target document
    #

    if offset != num_target_pages:
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

def create_asset_from_stream( data_stream, **kwargs ):

    """ Create a page view work item on the output channel (given by name)
        from the passed data stream.

    """
    logging.debug(
        'Creating Asset<%s>' % ', '.join(
            '%s=%s' % n_v for n_v in kwargs.iteritems() ) )

    asset = manager(Asset).create(**kwargs)

    logging.info('Uploading %r' % asset)

    s3.upload_from_stream( asset.s3_key, data_stream, asset.mime_type.name )

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

def publish_work_item( *asset_list ):

    """ Broadcast messages about the existence or modification of an set
        of assets to the relevant listening services.sq

    """
    logging.info(
        'Queuing work items:%s' % ''.join( '\n  %r' % a for a in asset_list ))

    sqs.post_message_list(
        ( {  'Asset-ID'     : asset.pk,
             'Process-Name' : consumer.name }
          for asset in asset_list
          for consumer in asset.consumers ) )


###############################################################################

def retrieve_work_item(
    visibility_timeout = None,
    max_wait_time      = None,
    interrupt_func     = None ):

    """ Retrieve the next work item for the given processor.

    """

    temp_dir = tempfile.mkdtemp(
        prefix = 'donomo-work-item-',
        dir    = settings.TEMP_DIR )

    try:
        message = sqs.get_message(
            visibility_timeout = visibility_timeout,
            max_wait_time      = max_wait_time,
            interrupt_func     = interrupt_func )

        if message is None:
            return None

        asset = manager(Asset).get( pk = message['Asset-ID'] )

        message.update(
            s3.download_to_file(
                s3_source_path = asset.s3_key,
                local_dest_path = os.path.join(temp_dir, asset.file_name)))

        message.update(
            { 'Asset-Instance' : asset,
              'Asset-Class'    : asset.asset_class,
              'Owner'          : asset.owner,
              })

        logging.info(
            'Retrieved work item: '         \
                'process=%(Process-Name)s,' \
                'asset=%(Asset-Instance)r'  \
                % message)

        return message

    except:
        logging.exception("Failed to retrieve work item")
        shutil.rmtree(temp_dir)
        return None

###############################################################################

def close_work_item(work_item, delete_from_queue):

    """
    Finish handling the given work_item, deleting it from the input
    queue if delete_from_queue is true

    """

    logging.info(
        "%s %r" % (
            (delete_from_queue and ' closing ' or ' aborting '),
            work_item['Asset-Instance'] ))

    local_path = work_item['Local-Path']

    if delete_from_queue:
        sqs.delete_message(work_item)

    if os.path.exists(local_path):
        shutil.rmtree(os.path.dirname(local_path))

###############################################################################

