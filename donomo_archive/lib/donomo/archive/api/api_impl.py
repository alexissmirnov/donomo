"""
AJAX API Views.

"""
#
# pylint: disable-msg=C0103,W0702
#
#   C0103 - variables at module scope must be all caps
#   W0702 - catch exceptions of unspecifed type
#
from cStringIO                       import StringIO
from django.conf                     import settings
from django.contrib.auth             import authenticate, login
from django.contrib.auth.decorators  import login_required
from django.contrib.auth.models      import User
from django.db.models                import ObjectDoesNotExist
from django.http                     import HttpResponse, HttpRequest, HttpResponseRedirect
from donomo.archive                  import models
from donomo.archive.operations       import instantiate_asset
from donomo.archive.service          import indexer
from donomo.archive.utils            import pdf, s3
from donomo.archive.utils.http       import HttpRequestValidationError, HttpResponseCreated
from donomo.archive.utils.middleware import long_poll, json_view, JSON_CONTENT_TYPE
from donomo.archive.utils.misc       import get_url, param_is_true, guess_mime_type, humanize_date
from donomo.archive.utils.sync       import update_sync_config
from donomo.billing.models           import get_remaining_credit
import email.utils
import datetime
import json
import logging
import os
import shutil
import tempfile
import uuid
import zipfile

__all__ = (
    'upload_document',
    'split_document',
    'merge_documents',
    'get_document_list',
    'get_document_info',
    'get_document_pdf',
    'get_document_zip',
    'update_document',
    'delete_document',
    'get_page_info',
    'get_page_view',
    'delete_page',
    'get_tag_list',
    'get_tag_info',
    'delete_tag',
    'tag_documents',
    'get_page_pdf',
    'get_search',
    'process_uploaded_files',
    'get_message_list',
    'get_conversation_list',
    'get_conversation_info',
    'get_contact_list',
    'get_message_info',
    'get_message_list',
    'update_or_create_account',
    )

logging = logging.getLogger('web-api')


DEFAULT_PAGE_VIEW_NAME = 'thumbnail'


##############################################################################

def _init_processor():
    return operations.initialize_processor(
        'web-api',
        default_inputs  = (),
        default_outputs = (
            models.AssetClass.UPLOAD,
            ),
        default_accepted_mime_types = (
            models.MimeType.JPEG,
            models.MimeType.PDF,
            models.MimeType.TIFF,
            ))

##############################################################################

def refreshed( instance ):

    """ Return a fresh copy of this instance (i.e., not cached).  This is
        handy if we're previously made some change in the db without
        going through the instance.  For example, using custom SQL.

    """

    return instance.objects.select_related().get( pk = instance.pk )


##############################################################################

def page_as_json_dict( page, view_name, only_api_url = False):

    """ Helper function to transform a page into a dictionary, suitable
        for transliteration into JSON.

    """

    if only_api_url:
        return { 'url' : get_url('api_page_info', pk = page.pk) }

    return {
        'id'       : page.pk,
        'url'      : get_url('api_page_info', pk = page.pk),
        'owner'    : page.owner.pk,
        'document' : get_url('api_document_info', pk = page.document.pk),
        'position' : page.position,
        'pdf_url'  : get_url('api_page_as_pdf', pk = page.pk ),
        'view'     : get_url('api_page_view', pk = page.pk, view_name = view_name),
        }


##############################################################################

def document_as_json_dict( document, page_view_name, page_num_list = None ):
    """
    Helper function to transform a document into a dictionary.  Handy for
    being further transformed into JSON.
    """

    if page_num_list is None:
        page_set = []
    elif page_num_list == 'all':
        page_set = document.pages.order_by('position').all()
    else:
        page_set = document.pages.order_by('position').filter(
            position__in = page_num_list)

    tags = [ tag.label for tag in document.tags.all() ]
    json = {
        'owner'  : document.owner.pk,
        'url'    : get_url('api_document_info', pk = document.pk),
        'title'  : document.title,
        'tags'   : tags,
        'tags_string' : ' '.join(tags),
        'length' : document.num_pages,
        'thumbnail' : '',
        'pdf'    : get_url('api_document_as_pdf', pk = document.pk),
        'pages'  : [ page_as_json_dict(
                                       page,
                                       page_view_name) for page in page_set ],
        }

    if document.pages.count() > 0:
        json['thumbnail'] = get_url(
            'api_page_view',
            pk = document.pages.get(position=1).pk,
            view_name = page_view_name)

    return json

##############################################################################

def tag_as_json_dict(
    tag,
    date = None,
    show_doc_count = False,
    show_documents = False,
    show_contacts  = False,
    show_conversations = False,
    show_message_bodies = False,
    show_url       = False,
    relative_time  = False,
    view_name      = models.AssetClass.PAGE_THUMBNAIL,
    show_id        = True ):

    """
    Helper function to express a tag as a dictionary suitable for
    conversion to JSON.

    """
    if relative_time and tag.tag_class == models.Tag.UPLOAD_AGGREGATE:
        name = humanize_date(tag.label.split('.')[0])
    else:
        name = tag.label

    out_dict  = {'name' : name, 
                 'label' : tag.label, 
                 'date' : str(date),
                 'tag_class' : tag.tag_class }

    if show_url:
        out_dict.update( url = get_url('api_tag_info', label = tag.label) )

    if show_conversations:
        conversations = tag.conversations.all()
        out_dict.update(
                conversations = [
                    conversation_as_json_dict(conversation, show_message_bodies)
                    for conversation in conversations ] )
        
    if show_doc_count or show_documents:
        documents = tag.documents.all()

        if show_documents:
            out_dict.update(
                documents = [
                    document_as_json_dict(document, view_name)
                    for document in documents ] )

        if show_doc_count:
            out_dict.update(document_count = documents.count())

    if show_id:
        out_dict.update(guid = '%s.tag' % tag.pk)
        
    return out_dict

##############################################################################

def extract_tag_list(request):
    """
    Helper function to pull out a list or tag labels from the request.
    The labels may either be in a comma or semicolon seperated list in
    a single field called 'tags' or specified individually in a
    multiply-occuring field called 'tag'.

    This function will ensure that all tags requested exist in the
    database.

    """

    label_list = None

    if request.POST.has_key('tags'):
        label_list = request.POST['tags'].split(';,')

    if request.POST.has_key('tag'):
        label_list = (label_list or []).extend(request.POST.getlist('tag'))

    if label_list is not None:
        return models.Tag.objects.get_or_create_from_label_list(
            request.user,
            label_list )

    return None

##############################################################################

def extract_query_string(request):
    """
    Helper function to pull out the query string (or None) if present
    and not empty in the request.

    """
    query_string = None
    if request.REQUEST.has_key('q'):
        candidate = request.REQUEST['q'].strip()
        if len(candidate) != 0:
            query_string = candidate
    return query_string


##############################################################################
@login_required
@json_view
def get_document_list(request):
    """
    Retrieve the document list, optionally restricting the list to those
    documents matching some query.

    """

    # TODO: take num_rows from user preferences

    start_index  = int(request.REQUEST.get('start_index', 0))
    num_rows     = int(request.REQUEST.get('num_rows', 250))
    page_view_name = request.REQUEST.get('view_name', DEFAULT_PAGE_VIEW_NAME)

    all_docs = request.user.documents.all()
    doc_list = all_docs [ start_index : start_index+num_rows ]

    return {
        'start_index' : start_index,
        'all_documents_count' : len(all_docs),
        'documents' : [ document_as_json_dict(
                  doc,
                  page_view_name, [1]) for doc in doc_list ],
        }

##############################################################################

@json_view
def upload_document(request):
    """
    Upload a new document.

    """
    logging.debug('upload_document')
    username = request.POST['user']
    password = request.POST['password']
    logging.debug('username=%s'%username)
    request.user = authenticate(username=username, password=password)

    if request.user is None or not request.user.is_active:
        raise HttpRequestValidationError('account disabled')

    # check if user's account isn't running low
    if not get_remaining_credit(request.user):
        return { 'status' : 402, # payment required
                }

    process_uploaded_files(request.FILES, request.user)

    return {
        'status'   : 202,
        # 'location' : upload.get_absolute_url(),
        }

def process_uploaded_files(files, user):
    gateway      = _init_processor()[0]
    logging.debug(str(gateway))

    # pick all files that are send in this API
    # support sending multiple files in a single request
    for key, the_file in files.iteritems():
        content_type = the_file.content_type

        if content_type == 'application/octet-stream':
            content_type = guess_mime_type(the_file.name)

        asset_class  = models.manager(models.AssetClass).get(name = models.AssetClass.UPLOAD)

        if not asset_class.has_consumers(content_type):
            raise HttpRequestValidationError(
                'Unsupported content type: %s' % content_type)

        upload = operations.create_asset_from_stream(
            data_stream  = StringIO(the_file.read()),
            owner        = user,
            producer     = gateway,
            asset_class  = models.AssetClass.UPLOAD,
            file_name    = the_file.name,
            child_number = 0,
            mime_type    = content_type)

        operations.publish_work_item(upload)

##############################################################################
@login_required
@json_view
def split_document(request):
    """
    Create a new document from the given existing document, starting from the
    page given.  This is a "split" document operation.

    """
    page_view_name = request.REQUEST.get('view_name', DEFAULT_PAGE_VIEW_NAME)
    old_document = request.user.documents.get(pk = int(request.REQUEST['id']))
    new_document = operations.split_document(
        old_document,
        int( request.REQUEST['split_after_page'] ))

    # TODO: what work items are generated by spliting a document?

    return {
        'original_document' : document_as_json_dict(old_document, page_view_name, 'all'),
        'new_document'       : document_as_json_dict(new_document, page_view_name, 'all'),
        }

##############################################################################
@login_required
@json_view
def merge_documents(request):
    """
    Insert the source document into the target document starting at the
    given position.

    """
    target = request.user.documents.get(pk = int(request.REQUEST['tgt_id']))
    source = request.user.documents.get(pk = int(request.REQUEST['src_id']))
    offset = (request.REQUEST.has_key('offset') and int(request.REQUEST['offset'])) or None
    page_view_name = request.REQUEST.get('view_name', DEFAULT_PAGE_VIEW_NAME)

    operations.merge_documents(target, source, offset)

    # TODO: what work items are generated by merging two documents?

    return {
        'document' : document_as_json_dict(target, page_view_name),
        }

##############################################################################

@json_view
def get_document_info(request, pk):
    """
    Get a JSON representation of document.

    """
    document = request.user.documents.get(pk = pk)
    page_view_name = request.REQUEST.get('view_name', DEFAULT_PAGE_VIEW_NAME)

    return {
        'document' : document_as_json_dict(document, page_view_name, 'all'),
        }

##############################################################################

def get_document_pdf(request, pk):
    """
    Retrieve a document by primary key, as a PDF file.  Note that this
    is not a JSON view.

    """
    document = request.user.documents.get(pk = pk)
    assets = document.assets.filter(
        asset_class__name = models.AssetClass.DOCUMENT,
        mime_type__name   = models.MimeType.PDF )

    if len(assets) != 0:
        meta = operations.instantiate_asset(assets[0])
        try:
            response = HttpResponse(open(meta['Local-Path'], 'rb'))
            response['Content-Disposition'] = \
                'attachment; filename=doc-%d.pdf' % document.pk
            response['Content-Type']   = meta['Content-Type']
            response['Content-Length'] = os.stat(meta['Local-Path']).st_size
            response['ETag' ]          = meta['ETag' ]
            response['Last-Modified']  = meta['Last-Modified']
        finally:
            shutil.rmtree(os.path.dirname(meta['Local-Path']))
    else:
        response = HttpResponse(content_type = 'application/pdf')
        response['Content-Disposition'] = \
        'attachment; filename=doc-%d.pdf' % document.pk
        pdf.render_document(document, response, request.user.username, str(document.pk))

    return response

##############################################################################

def get_document_zip(request):
    """
    Returns .zip archive as an attachment in HTTP response. The archive
    contains PDFs of documents specified in comma-separated "ids".
    If "ids" parameter isn't specified, a comma separated "tags" parameter
    is used to archive all document that belong to any of the tag.
    """
    temp_dir = ''

    # Get a list of all document IDs we need to pack into an archive
    # TODO: what is a document is tagged with multiple tags?
    if request.REQUEST.has_key('ids'):
        keys = request.REQUEST['ids'].split(',')
    elif request.REQUEST.has_key('tags'):
        keys = list()
        for tag in request.REQUEST['tags'].split(','):
            tag = request.user.tags.get(label = tag)
            for doc in tag.documents.all():
                keys.append(doc.pk)

    try:
        temp_dir = tempfile.mkdtemp(
            prefix = 'donomo-document-zip-',
            dir    = settings.TEMP_DIR )

        # Create a zip file
        zip_path_name = os.path.join(temp_dir, 'donomo-documents.zip')
        zip_file = zipfile.ZipFile(zip_path_name, 'w', zipfile.ZIP_STORED, True)

        # iterate over every document id
        for pk in keys:
            pk = int(pk)
            document = request.user.documents.get(pk = pk)

            # Get a PDF asset and download it
            pdf_asset = document.assets.get(
                asset_class__name = models.AssetClass.DOCUMENT,
                mime_type__name   = models.MimeType.PDF)

            pdf_asset_metadata = operations.instantiate_asset(pdf_asset, temp_dir)

            # add the downloaded file into the archive
            zip_file.write(pdf_asset_metadata['Local-Path'], 'doc-%s.pdf' % document.pk)

        zip_file.close()

        zip_file_size = os.stat(zip_path_name).st_size
        zip_file = open(zip_path_name, 'rb')

        response = HttpResponse(zip_file)
        response['Content-Length'] = zip_file_size
        response['Content-Type'] = 'application/x-zip-compressed'
        response['Content-Disposition'] = \
            'attachment; filename=donomo-documents.zip'

        return response

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

##############################################################################

@json_view
def update_document(request, pk):
    """
    Update a document.  Accepts 'title' and/or a 'tags' or multiple 'tag'
    parameters.

    """
    document = request.user.documents.get( pk = pk )

    new_tag_list = extract_tag_list(request)
    if new_tag_list is not None:
        document.tags = new_tag_list

    if request.REQUEST.has_key('title'):
        document.title = request.REQUEST['title']
        document.save()

    return {
        'document' : document_as_json_dict(document, DEFAULT_PAGE_VIEW_NAME),
        }

##############################################################################

@json_view
def delete_document(request, pk):
    """
    Delete a document.

    """
    request.user.documents.get(pk = pk).delete()

    # TODO: clean up stuff related to the document

    return {}

##############################################################################

@json_view
def get_page_info(request, pk):
    """
    Retrieve a page

    """
    view_name = request.REQUEST.get('view_name', 'image')
    return {
        'page' : page_as_json_dict(
                                   request.user.pages.get( pk = int(pk) ),
                                   view_name),
        }

##############################################################################

def get_page_view(request, pk, view_name):
    """
    Retrieve a view (asset) for a page

    """
    page = request.user.pages.get(pk = int(pk))
    asset = page.assets.get(asset_class__name = view_name)
    data = operations.instantiate_asset(asset)
    stream = open(data['Local-Path'], 'rb')
    resp = HttpResponse(stream)
    resp['Content-Type'] = data['Content-Type']
    resp['ETag' ] = data['ETag' ]
    resp['Content-Length'] = os.stat(data['Local-Path']).st_size
    resp['Last-Modified'] = data['Last-Modified']
    shutil.rmtree(os.path.dirname(data['Local-Path']))
    return resp

##############################################################################

def get_page_pdf(request, pk):
    """
    Returns a PDF of a given page. Not a JSON view
    """
    page = request.user.pages.get(pk = pk)

    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = \
        'attachment; filename=doc-%d-page-%s-of-%s.pdf' \
            % (page.document.pk,
               page.position,
               page.document.num_pages)

    pdf.render_page(page, response, request.user.username, str(page))

    return response

##############################################################################

@json_view
def delete_page(request, pk):
    """
    Delete a document.

    """
    request.user.pages.get(pk = pk).delete()
    # TODO: delete from index
    return {}

##############################################################################
@long_poll
@json_view
def get_tag_list(request):
    """
    Get a list of the user's tags, optionally starting with some
    initial pattern.  The request can specifiy whether it just wants
    the play list of labels (the default), or it can request the the
    number of documents belonging to the tag is included, plus the URL
    for each tag, plus document info for each tag.

    """
    exclude_prefix = request.REQUEST.get('notstartswith', None)
    prefix     = request.REQUEST.get('startswith', None)
    show_count = param_is_true(request.REQUEST.get('doc_count', 'false'))
    show_conversations = param_is_true(request.REQUEST.get('conversations', 'false'))
    show_message_bodies = param_is_true(request.REQUEST.get('message_bodies', 'false'))
    show_url   = param_is_true(request.REQUEST.get('url', 'false'))
    relative_time = param_is_true(request.REQUEST.get('relative_time', 'true'))

    if prefix:
        tag_set = request.user.tags.filter(label__istartswith=prefix.lower())
    else:
        tag_set = request.user.tags.all()
        
    if exclude_prefix:
        tag_set = set(tag_set)
        exclude_tag_set = set(request.user.tags.filter(label__istartswith=exclude_prefix.lower()))
        tag_set = tag_set.difference(exclude_tag_set)

    tag_list = list()
    
    for t in tag_set:
        if t.conversations.count() > 0:
            tag_list.append({'date': t.conversations.order_by('messages__date')[0].date, 'tag': t})
    tag_list.sort(reverse=True)
    
    return {
        'content' : [
            tag_as_json_dict(
                list_entry['tag'],
                date = list_entry['date'],
                show_doc_count = show_count,
                show_documents = False,
                show_conversations = show_conversations,
                show_message_bodies = show_message_bodies,
                show_url       = show_url,
                relative_time  = relative_time )
            for list_entry in tag_list ],
        }
    
        
##############################################################################

@json_view
def tag_documents(request, label):
    """
    Bulk add documents to a tag, by document pk specified in a multiple
    'doc' fields in the request body.

    """
    tag = models.Tag.objects.get_or_create(
        owner = request.user,
        label = label.lower(),
        tag_class = models.Tag.USER) [0]

    if 'doc' not in request.POST:
        logging.debug("raise KeyError('at least one document is requried')")
    else:
        doc_pk_list = request.POST.getlist('doc')
    
        documents = request.user.documents.filter(
            pk__in = [ int(pk) for pk in doc_pk_list ] )
    
        if len(documents) != len(doc_pk_list):
            raise ObjectDoesNotExist(
                'One or more of the document pks given is invalid')
    
    
        tag.documents.add(documents)

    return tag_as_json_dict(tag)

##############################################################################

@json_view
def get_tag_info(request, label):
    """
    Get the set of documents associated with a tag

    """
    return tag_as_json_dict(
        request.user.tags.get(label = label.rstrip().lower()),
        show_doc_count = True,
        show_documents = True,
        show_conversations = param_is_true(request.REQUEST.get('conversations', 'false')),
        show_url       = param_is_true(request.REQUEST.get('show_url', 'false')),
        relative_time  = param_is_true(request.REQUEST.get('relative_time', 'true')))


##############################################################################

@json_view
def delete_tag(request, label):
    """
    Delete a tag.  This untags (but does not delete) any documents
    currently bearing the tag.

    """
    request.user.tags.get(label = label.rstrip().lower()).delete()
    return {}

##############################################################################

@json_view
def get_search(request):
    """
    Returns the search results.
    """
    query_string = extract_query_string(request)
    start_index  = int(request.REQUEST.get('start_index', 0))
    num_rows     = int(request.REQUEST.get('num_rows', 250))
    page_view_name = request.REQUEST.get('view_name', DEFAULT_PAGE_VIEW_NAME)
    search_results = indexer.query(
            request.user,
            query_string,
            start_index,
            num_rows)

    # transform 'docs' collection returned by indexer
    # into pages collection
    # once the transformation is done we don't need 'docs' section
    # so we delete it
    search_results['pages'] = []

    for d in search_results['results']['docs']:
        page = models.Page.objects.get(pk = d['page_id'])
        page_json = page_as_json_dict(page, page_view_name)
        page_json['hits'] = d['hits']
        page_json['height'] = d['page_height']
        page_json['width'] = d['page_width']

        search_results['pages'].append(page_json)

    del(search_results['results'])
    return search_results


##############################################################################

@json_view
def get_message_list(request):
    """
    Get a list of the user's messages
    """
    message_set = [{'body': 'this is message body'}, 
                   {'body': 'this is another message body'}]

    return {
        'content' : [ message_as_json_dict( message ) 
                     for message in message_set ],
        }

def conversation_as_json_dict(conversation, 
                              message_body = True):
    messages = conversation.messages.all().order_by('-date')
    json = {
        'guid'      : '%s.conversation' % conversation.pk,
        'subject'   : conversation.subject,
        'summary'   : conversation.summary,
        'date'      : humanize_date(messages[0].date),
        'tags'     : [ '%s.tag' % tag.pk 
                       for tag in conversation.tags.all() ],
        'key_participant' : {
            'email' : conversation.key_participant.email,
            'contact' : '%s.contact' % conversation.key_participant.contact.pk }
        }
    if message_body:
        json.update(messages = [ message_as_json_dict(message, message_body)
                       for message in messages])
    else:
        json.update(messages = [ '%s' % message.pk
                       for message in messages])
        
    return json


@long_poll
@json_view
def get_conversation_list(request):
    """
    Gets all conversations
    """
    conversation_set = request.user.conversations.all()
    show_message_body  = bool(request.REQUEST.get('message_body', False))
    return {
            'content' : [ conversation_as_json_dict(conversation,
                                                    show_message_body)
                    for conversation in conversation_set ],
    }

@json_view
def get_conversation_info(request, id):
    """
    Gets all conversations
    """
    id = id.split('.')[0] # strip the '.conversation' at the end of the id
    conversation = request.user.conversations.get(pk = id)
    return conversation_as_json_dict(conversation)
    
def contact_as_json_dict(contact):
    json = {
        'guid'      : '%s.contact' % contact.pk,
        'name'      : contact.name,
        'addresses' : [ { 'email' : address.email }
                       for address in contact.addresses.all() ],
        'tags'     : [ '%s.tag' % tag.pk 
                       for tag in contact.tags.all() ],
        }
    
    
    return json

@json_view
def get_contact_list(request):
    """
    Gets all conversations
    """
    contact_set = request.user.contacts.all()
    return {
            'content' : [ contact_as_json_dict(contact)
                    for contact in contact_set ],
    }
    
def message_as_json_dict(message, include_body = True):
    """
    Serializes message metadata and (optionnaly) message body into JSON
    """
    json = {
        'guid'                  : message.pk,
        'subject'               : message.subject,
        'sender_address'        : message.sender_address.email,
        'date'                  : message.date.ctime()
        }

    if include_body:
        body_type = models.MimeType.HTML
        message_asset = message.get_asset(models.AssetClass.MESSAGE_PART, 
                                          body_type)
        if not message_asset:
            body_type = models.MimeType.TEXT
            message_asset = message.get_asset(models.AssetClass.MESSAGE_PART, 
                                              body_type)
        if message_asset:
            message_file = instantiate_asset(message_asset)['Local-Path']
            message_text = open(message_file,'r').read()
        
            #TODO: figure out why a message has some non-ascii chars
            # i need to call decode here
            message_text = message_text.decode('utf8','ignore')

            #TODO: extract the message from conversation. 
            # This will be much more complex than looking for -----Original Message-----
            if body_type == models.MimeType.TEXT:
                json.update(body = message_text.split('-----Original Message-----')[0])
            else:
                json.update(body = message_text)
            json.update(body_type = body_type)
            
    return json
    
@json_view
def get_message_info(request, id):
    """
    Gets all conversations
    """
    include_body  = bool(request.REQUEST.get('body', True))

    message = request.user.messages.get(pk = id)
    json = message_as_json_dict(message, include_body)
    return json


@long_poll
@json_view
def get_message_list(request):
    """
    Get messages along with metadata
    """
    include_conversations = bool(request.REQUEST.get('conversations', True))
    include_contacts = bool(request.REQUEST.get('contacts', True))
    include_tags = bool(request.REQUEST.get('tags', True))
    
    limit = int(request.REQUEST.get('limit', 10))
    
    modified_since = request.REQUEST.get('modified_since', 
                                         None) or request.META.get('If-Modified-Since', 
                                                                   None)
    if modified_since: 
        modified_since = datetime.datetime(*email.utils.parsedate(modified_since)[:6])
        
    modified_before = request.REQUEST.get('modified_before', None)
    if modified_before: 
        modified_before = datetime.datetime(*email.utils.parsedate(modified_before)[:6])
    
    if modified_since and modified_before:
        messages = request.user.messages.filter(date__gte = modified_since, date__lt = modified_before)
    elif modified_since:
        messages = request.user.messages.filter(date__gte = modified_since)
    elif modified_before:
        messages = request.user.messages.filter(date__lt = modified_before)
    else:
        messages = request.user.messages.all()
        
    message_count = messages.count()
    messages = messages.order_by('-date')[:limit]
    
    conversation_set = set()
    tag_set = set()
    contact_set = set()
    address_set = set()
    
    for message in messages:
        conversation_set.add(message.conversation)
        tag_set.update(set(message.conversation.tags.all()))
        address_set.update(set(message.to_addresses.all()))
        address_set.update(set(message.cc_addresses.all()))
        address_set.add(message.sender_address)
    
    for address in address_set:
        contact_set.add(address.contact)
        
    return {
            'message_count' : message_count,
            'message_limit' : limit,
            'messages' : [ message_as_json_dict(message)
                    for message in messages ],
                    
            'conversations' : [ conversation_as_json_dict(conversation, False)
                    for conversation in conversation_set ],
            'tags' : [ tag_as_json_dict(tag)
                    for tag in tag_set ],
            'contacts' : [ contact_as_json_dict(contact)
                    for contact in contact_set ],
    }    

        
def update_or_create_account(request, id):
    """
    Handles PUT /accounts/<id>/
    
    May create new or update an existing account identified by ID.
    
    This method also does lazy-creation of user objects.
    
    Each account must be associated to a user object. If a user object
    isn't supplied this means we're dealing with the first-time signup.
    
    """
    username = request.REQUEST.get('username', None)
    if not username:
        # No username? Let's create one and log it in.
        # username is in reality a unique secret key shared with the client
        username = str(uuid.uuid4())
        user = User.objects.create_user(username, username, username)
        user = authenticate(username=user.username, password=user.username)
        user.save()
    else:
        # Username provided? Then it must be found in the db
        user = User.objects.get(username=username)
        
    user = authenticate(username=user.username, password=user.username)
    if user is not None:
        if user.is_active:
            login(request, user)
        else:
            #TODO Return a 'disabled account' error message
            pass
    else:
        #TODO Return an 'invalid login' error message
        pass
        
    #load json from the request body
    body = json.loads(request.raw_post_data)
    
    #TODO: validate the account credentials with the external service
    
    account_class, created = models.AccountClass.objects.get_or_create(name = body['accountClass'])
    account, created = models.Account.objects.get_or_create(id = id, 
                                  defaults={'owner': user,
                                            'account_class': account_class,
                                            'name': body['name'],
                                            'password': body['password']})
    
    if created:
        response = HttpResponseCreated(request.get_host() + request.path)
        response.content = json.dumps( {'username' : username} )
        response.content_type = JSON_CONTENT_TYPE
    else:
        account.name = body['name']
        account.password = body['password']
        account.save()
        response = HttpResponse()
    
    if not update_sync_config(account):
        raise HttpRequestValidationError('Invalid account (only Gmail is supported at the moment)')

    return response

