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
from django.core.validators          import ValidationError
from django.db.models                import ObjectDoesNotExist
from django.http                     import HttpResponse, HttpResponseRedirect
from donomo.archive                  import models, operations
from donomo.archive.service          import ProcessDriver, indexer
from donomo.archive.utils            import pdf as pdf_utils
from donomo.archive.utils            import s3 as s3_utils
from donomo.archive.utils.middleware import json_view
from donomo.archive.utils.misc       import get_url, param_is_true

import logging

__all__ = (
    'upload_document',
    'split_document',
    'merge_documents',
    'get_document_list',
    'get_document_info',
    'get_document_view',
    'update_document',
    'delete_document',
    'get_page_info',
    'get_page_view',
    'delete_page',
    'get_tag_list',
    'get_tag_info',
    'delete_tag',
    'tag_documents',
    )

logging = logging.getLogger('web-api')

# ---------------------------------------------------------------------------

class WebGateway(ProcessDriver):
    """
    Adapter to allow the web-site to participate as a processor.

    """

    SERVICE_NAME    = 'web'

    DEFAULT_OUTPUTS = (
        ( 'upload', ['donomo.archive.service.tiff_parser']),
        )

    ACCEPTED_CONTENT_TYPES = (
        'image/tiff',
        )

    def handle_work_item(self, work_item):
        """
        The gateway should never be run as a processor
        """
        raise Exception(
            'The web gateway is not intended to run as a processor' )

# ---------------------------------------------------------------------------

def refreshed( instance ):
    """
    Return a fresh copy of this instance (i.e., not cached).  This is handy
    if we're previously made some change in the db without going through
    the instance.  For example, using custom SQL.

    """

    return instance.objects.select_related().get( pk = instance.pk )


# ---------------------------------------------------------------------------

def page_as_json_dict( page, page_view_name, only_api_url = False):
    """
    Helper function to transform a page into a dictionary, suitable for
    transliteration into JSON.

    """

    if only_api_url:
        return { 'url' : get_url('api_page_info', pk = page.pk) }

    logging.debug(get_url('api_document_info', pk = page.document.pk))
    
    return {
        'url'          : get_url('api_page_info', pk = page.pk),
        'owner'        : page.owner.pk,
        'document'     : get_url('api_document_info', pk = page.document.pk),
        'position'     : page.position,
        #TODO 'pdf_url'      : get_url('page_as_pdf', pk = page.pk ), -- this throws
        #TODO 'upload_date'  : page.upload.timestamp, -- this doesnt exist
        'thumbnail'    : get_url('api_page_view', 
                                 pk =  page.pk, 
                                 view_name = page_view_name),
        }


# ---------------------------------------------------------------------------

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

    return {
        'owner'  : document.owner.pk,
        'title'  : document.title,
        'tags'   : [ tag.label for tag in document.tags.all() ],
        'length' : document.num_pages,
        #TODO 'pdf'    : get_url('document_as_pdf', { 'id' : document.pk }), -- this throws!
        'pages'  : [ page_as_json_dict(page, page_view_name) for page in page_set ],
        }

# ----------------------------------------------------------------------------

def tag_as_json_dict(
    tag,
    show_doc_count = False,
    show_documents = False,
    show_url       = False ):

    """
    Helper function to express a tag as a dictionary suitable for
    conversion to JSON.

    """
    out_dict  = { 'name' : tag.label }

    if show_url:
        out_dict.update( url = get_url('api_tag_info', label = tag.label) )

    if show_doc_count or show_documents:
        documents = tag.documents.all()

        if show_documents:
            out_dict.update(
                documents = [
                    document_as_json_dict(document)
                    for document in documents ] )

        if show_doc_count:
            out_dict.update(document_count = documents.count())

    return out_dict

# ----------------------------------------------------------------------------

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
            request.owner,
            label_list )

    return None

# ----------------------------------------------------------------------------

def extract_query_string(request):
    """
    Helper function to pull out the query string (or None) if present
    and not empty in the request.

    """
    query_string = None
    if request.has_key('q'):
        candidate = request['q'].strip()
        if len(candidate) != 0:
            query_string = candidate
    return query_string


# ----------------------------------------------------------------------------

@json_view
def get_document_list(request):
    """
    Retrieve the document list, optionally restricting the list to those
    documents matching some query.

    """

    # TODO: take num_rows from user preferences

    query_string = extract_query_string(request)
    start_index  = int(request.GET.get('start_index', 0))
    num_rows     = int(request.GET.get('num_rows', 25))
    page_view_name = request.GET.get('view_name', 'jpeg-thumbnail-200')
    
    if query_string is not None:
        return indexer.query(
            request.user,
            query_string,
            start_index,
            num_rows)
    else:
        all_docs = request.user.documents.all()
        doc_list = all_docs [ start_index : num_rows ]
        return {
            'query' : query_string,
            'documents' : [ document_as_json_dict(doc, page_view_name, [1]) for doc in doc_list ],
            }

# ----------------------------------------------------------------------------

@json_view
def upload_document(request):
    """
    Upload a new document.

    """

    gateway      = WebGateway()
    the_file     = request.FILES['file']
    content_type = the_file['content-type']

    if not gateway.handles_content_type( content_type ):
        raise ValidationError(
            'Unsupported content type: %s' % content_type)

    upload = operations.create_upload_from_stream(
        gateway.processor,
        request.user,
        StringIO( the_file['content'] ),
        content_type )

    return {
        'status'   : 201,
        'location' : upload.get_absolute_url(),
        }

# ----------------------------------------------------------------------------

@json_view
def split_document(request):
    """
    Create a new document from the given existing document, starting from the
    page given.  This is a "split" document operation.

    """
    old_document = request.user.documents.get(pk = int(request['id']))
    new_document = operations.split_document(
        old_document,
        int( request['split_after_page'] ))

    return {
        'original-document' : document_as_json_dict(refreshed(old_document)),
        'new_docment'       : document_as_json_dict(refreshed(new_document)),
        }

# ----------------------------------------------------------------------------

@json_view
def merge_documents(request):
    """
    Insert the source document into the target document starting at the
    given position.

    """
    target = request.user.documents.get(pk = int(request['tgt_id']))
    source = request.user.documents.get(pk = int(request['src_id']))
    offset = (request.has_key('offset') and int(request['offset'])) or None

    operations.merge_documents(target, source, offset)

    return {
        'document' : document_as_json_dict(refreshed(target)),
        }

# ----------------------------------------------------------------------------

@json_view
def get_document_info(request, pk):
    """
    Get a JSON representation of document.

    """
    document = request.user.document.get(pk = pk)
    return {
        'document' : document_as_json_dict(document),
        }

# ----------------------------------------------------------------------------

def get_document_view(request, pk):
    """
    Retrieve a document by primary key, as a PDF file.  Note that this
    is not a JSON view.

    """

    document = request.user.document.get(pk = pk)
    return HttpResponse(
        content = pdf_utils.render_document(document),
        content_type = 'application/pdf' )

# ----------------------------------------------------------------------------

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

    if request.has_key('title'):
        document.title = request['title']
        document.save()

    return {
        'document' : document_as_json_dict(document),
        }

# ----------------------------------------------------------------------------

@json_view
def delete_document(request, pk):
    """
    Delete a document.

    """
    request.user.document.get(pk = pk).delete()
    return {}

# ----------------------------------------------------------------------------

@json_view
def get_page_info(request, pk):
    """
    Retrieve a page

    """
    return {
        'page' : page_as_json_dict( request.user.pages.get( pk = pk )),
        }

# ----------------------------------------------------------------------------

def get_page_view(request, pk, view_name):
    """
    Retrieve a view of a page

    """
    page = request.user.pages.get(pk = pk)

    if view_name != 'pdf':
        return HttpResponseRedirect(
            s3_utils.get_url(
                key        = page.get_s3_key(view_name),
                method     = 'GET',
                expires_in = settings.S3_ACCESS_WINDOW ))

    return HttpResponse(
        content = pdf_utils.render_page(page),
        content_type = 'application/pdf' )

# ----------------------------------------------------------------------------

@json_view
def delete_page(request, pk):
    """
    Delete a document.

    """
    request.user.pages.get(pk = pk).delete()
    # TODO: delete from index
    return {}

# ----------------------------------------------------------------------------

@json_view
def get_tag_list(request):
    """
    Get a list of the user's tags, optionally starting with some
    initial pattern.  The request can specifiy whether it just wants
    the play list of labels (the default), or it can request the the
    number of documents belonging to the tag is included, plus the URL
    for each tag, plus document info for each tag.

    """
    prefix     = request.GET.get('startswith', None)
    show_count = param_is_true(request.GET.get('show_count', 'false'))
    show_url   = param_is_true(request.GET.get('show_url', 'false'))

    if prefix:
        tag_set = request.user.tags.filter(istartswith=prefix.lower())
    else:
        tag_set = request.user.tags.all()

    return {
        'tags' : [
            tag_as_json_dict(
                tag,
                show_doc_count = show_count,
                show_url       = show_url,
                show_documents = False )
            for tag in tag_set ],
        }

# ----------------------------------------------------------------------------

@json_view
def tag_documents(request, label):
    """
    Bulk add documents to a tag, by document pk specified in a multiple
    'doc' fields in the request body.

    """
    if 'doc' not in request.POST:
        raise KeyError('at least one document is requried')

    doc_pk_list = request.POST.getlist('doc')

    documents = request.user.documents.filter(
        pk__in = [ int(pk) for pk in doc_pk_list ] )

    if len(documents) != len(doc_pk_list):
        raise ObjectDoesNotExist(
            'One or more of the document pks given is invalid')

    tag = models.Tag.objects.get_or_create(
        owner = request.user,
        label = label.lower()) [0]

    tag.documents.add(documents)

    return tag_as_json_dict(tag)

# ----------------------------------------------------------------------------

@json_view
def get_tag_info(request, label):
    """
    Get the set of documents associated with a tag

    """
    return tag_as_json_dict(
        request.user.tags.get(label = label.trim().lower()),
        show_doc_count = True,
        show_documents = True,
        show_url       = param_is_true(request.GET.get('show_url', 'false')))

# ----------------------------------------------------------------------------

@json_view
def delete_tag(request, label):
    """
    Delete a tag.  This untags (but does not delete) any documents
    currently bearing the tag.

    """
    request.user.tags.get(label = label.trim().lower()).delete()
    return {}

# ----------------------------------------------------------------------------
