from django.conf import settings
from docstore import log
from docstore.core import api as core_api
from docstore.core import utils as core_utils
from docstore.core.models import ViewType

import email
from cStringIO import StringIO

DEFAULT_OUTPUTS = (
    ( 'tiff-document', 'image/tiff', ['docstore.processor.attachment_parser']),
    )

def run_once():
    processor = core_api.get_or_create_processor(__name__, DEFAULT_OUTPUTS)

    #log.debug('getting next work item for processor %s' % processor)

    item = core_api.get_work_item(processor, 0)

    # nothing to work on for now - just exit
    if item is None:
        return False

    #??? do we need to open the file here or an item as a stream already?
    item_file = file(item['Local-Path'], 'r')
    msg = email.message_from_file(item_file)


    counter = 1
    for part in msg.walk():
        # multipart/* are just containers
        if part.get_content_type() != 'image/tiff':
            continue

        log.debug('part filename=%s content_type=%s' %(part.get_filename(), part.get_content_type()))

        filename = part.get_filename()
        if not filename:
            ext = mimetypes.guess_extension(part.get_content_type()) or '.bin'
            filename = 'part-%03d%s' % (counter, ext)
        counter += 1

        #??? an email may have multiple attachments, each will be represented
        # as a view. is it expected to set ViewType to content-type?
        # eg. image/tiff
        # or should it be something unique for every attachment like filename
        # eg. 123.tif

        core_api.create_doc_with_initial_view(
            processor,
            processor.outputs.get(name = 'tiff-document'),
            item['Object'].document.owner,
            item['Object'].document.title,
            StringIO(part.get_payload(decode=True)))


    core_api.close_work_item(item, True)
    log.info('done. parsed mail for document %s by %s' % (
        item['Object'].document.id,
        item['Object'].document.owner))

    return True



