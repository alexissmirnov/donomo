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
from django.conf                        import settings
from donomo.archive.models              import *
from donomo.archive.utils               import s3, sqs, misc
from donomo.archive.utils.http       import HttpRequestValidationError
from platform                           import node
from socket                             import gethostbyname, gaierror
from cStringIO                          import StringIO

import django.db
import os
import tempfile
import shutil
import logging
import subprocess
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

def create_document( owner, title = None):
    """
    Create a new document
    """

    if title is None:
        title = 'Created on %s' % strftime(
            "%Y-%m-%d %Y %H:%M:%S",
            gmtime())

    logging.info( 'Creating new document for %s: %s' % ( owner, title))

    document = manager(Document).create( title = title, owner = owner)

    create_asset_from_stream(
        data_stream = StringIO('empty'),
        file_name = 'empty.bin',
        owner = owner,
        asset_class = manager(AssetClass).get( name = AssetClass.DOCUMENT ),
        related_document = document,
        child_number = 0,
        mime_type = MimeType.BINARY )

    return document

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
        raise HttpRequestValidationError('Invalid merge position: %d' % offset)

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

ENCRYPT = 1
DECRYPT = 2

def secure_file( base_key, op, in_file_name, out_file_name ):
    """ Encrypt or decrypt a file on disk
    """
    passphrase = hmac.new(
        key = settings.SECRET_KEY,
        msg = '%s:%s' % (settings.DEPLOYMENT_MODE, base_key),
        digestmod = hashlib.sha1 ).hexdigest()

    params = {
        'cipher' : 'aes-192-cbc',
        'in'     : in_file_name,
        'out'    : out_file_name,
        'op'     : { ENCRYPT : 'e', DECRYPT : 'd' }[op],
        }

    process = subprocess.Popen(
        "openssl enc -%(op)s -%(cipher)s -pass stdin -in '%(in)s' -out '%(out)s' -salt" % params,
        shell     = True,
        stdin     = subprocess.PIPE,
        stdout    = subprocess.PIPE,
        stderr    = subprocess.PIPE,
        close_fds = True)

    (stdout, stderr) = process.communicate(passphrase)

    if process.returncode != 0:
        raise Exception(
            "Failed to %scrypt file\nOutput:\n%s\nError:\n%s" % (
                { ENCRYPT : 'en', DECRYPT : 'de' }[op],
                stdout,
                stderr ))

###############################################################################

def upload_asset_file( asset, orig_file_name ):
    """ Upload an asset file
    """
    keys = asset.owner.encryption_keys.all()
    if len(keys) == 0:
        file_name = orig_file_name
        logging.warn("%s is not secure" % asset.owner)
    else:
        file_name = '%s.enc' % orig_file_name
        secure_file(
            keys[0].value,
            ENCRYPT,
            orig_file_name,
            file_name )

    s3.upload_from_file(
        asset.s3_key,
        file_name,
        asset.mime_type.name )

    if file_name != orig_file_name:
        os.remove(file_name)

###############################################################################

def create_asset_from_stream( data_stream, **kwargs ):
    """ Create an asset given a file stream
    """
    on_disk = tempfile.NamedTemporaryFile()
    try:
        on_disk.write(data_stream.read())
        on_disk.flush()

        kwargs.setdefault('orig_file_name', kwargs.get('file_name'))
        kwargs['file_name'] = on_disk.name
        return create_asset_from_file( **kwargs )
    finally:
        on_disk.close()

###############################################################################

def create_asset_from_file( file_name, **kwargs ):

    """ Create a page view work item on the output channel (given by name)
        from the contents of the file denoted by path.

    """
    kwargs = kwargs.copy()
    kwargs.setdefault('orig_file_name', os.path.basename(file_name))
    kwargs.setdefault('mime_type', misc.guess_mime_type(file_name))

    logging.info(kwargs)
    
    asset = manager(Asset).create(**kwargs)
    upload_asset_file( asset, file_name)

    return asset

###############################################################################

def _enqueue_work_item( is_new, asset_list ):

    """ Broadcast messages about the existence or modification of an set
        of assets to the relevant listening services.

    """
    messages = list( {  'Asset-ID'     : asset.pk,
             'Process-Name' : consumer.name,
             'Is-New'       : is_new and 1 or 0 }
                  for asset in asset_list
                  for consumer in asset.consumers )

    logging.info(
        '%sueuing %d work items:%s' % (
            is_new and 'Q' or 'Re-q', len(messages), 
            ''.join( '\n  %r' % a for a in asset_list )))

    sqs.post_message_list( messages )

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

def instantiate_asset(asset, parent_temp_dir = None):

    """ Lookup the asset referenced by the message and instantiate a local
        copy of it.
    """

    if parent_temp_dir is None:
        parent_temp_dir = settings.TEMP_DIR

    temp_dir = tempfile.mkdtemp(
            prefix = 'donomo-work-item-',
            dir    =  parent_temp_dir )

    try:
        if not isinstance(asset, Asset):
            asset = manager(Asset).get( pk = asset )

        meta_data = {
            'Asset-Instance' : asset,
            'Asset-Class'    : asset.asset_class,
            'Owner'          : asset.owner,
            }

        file_name = os.path.join(temp_dir, asset.file_name)

        meta_data.update(
            s3.download_to_file(
                s3_source_path  = asset.s3_key,
                local_dest_path = file_name ))

        keys = asset.owner.encryption_keys.all()
        if len(keys) != 0:
            enc_name = '%s.enc' % file_name
            shutil.move(file_name, enc_name)
            secure_file(
                keys[0].value,
                DECRYPT,
    
                enc_name,
                file_name )
            os.remove(enc_name)

        logging.info( 'Instantiated %r' % asset )

        return meta_data

    except:
        logging.error(
            "Failed to retrieve work item: %s" % asset)
        shutil.rmtree(temp_dir)
        raise

###############################################################################

def retrieve_work_item(
    visibility_timeout = None,
    max_wait_time      = None,
    interrupt_func     = None,
    auto_get_asset     = True ):

    """ Retrieve the next work item from the queue.

    """

    try:

        if visibility_timeout is None:
            visibility_timeout = settings.SQS_VISIBILITY_TIMEOUT

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

