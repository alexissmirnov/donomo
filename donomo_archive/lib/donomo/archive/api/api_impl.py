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
from django.contrib.auth             import authenticate, login
from django.contrib.auth.decorators  import login_required
from donomo.archive                  import models, operations
from donomo.archive.service          import indexer
from donomo.archive.utils            import pdf, s3
from donomo.archive.utils.middleware import json_view
from donomo.archive.utils.misc       import get_url, param_is_true, guess_mime_type
import logging

__all__ = (
    'upload_document',
    'split_document',
    'merge_documents',
    'get_document_list',
    'get_document_info',
    'get_document_pdf',
    'update_document',
    'delete_document',
    'get_page_info',
    'get_page_view',
    'delete_page',
    'get_tag_list',
    'get_tag_info',
    'delete_tag',
    'tag_documents',
    'get_document_pdf',
    'get_page_pdf',
    'get_search',
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
    show_doc_count = False,
    show_documents = False,
    show_url       = False,
    view_name      = models.AssetClass.PAGE_THUMBNAIL ):

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
                    document_as_json_dict(document, view_name)
                    for document in documents ] )

        if show_doc_count:
            out_dict.update(document_count = documents.count())

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
    if request.has_key('q'):
        candidate = request['q'].strip()
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

    start_index  = int(request.GET.get('start_index', 0))
    num_rows     = int(request.GET.get('num_rows', 250))
    page_view_name = request.GET.get('view_name', DEFAULT_PAGE_VIEW_NAME)

    # Return all documents in inverse order of their primary key. 
    # FIXME: This is a hack because the order should be specified 
    # as part of the model
    all_docs = request.user.documents.all().order_by('-pk')
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
    user = authenticate(username=username, password=password)
    logging.debug(str(user))
    if user is not None:
        if user.is_active:
            login(request, user)
        else:
            raise ValidationError('account disabled')
    else:
        raise ValidationError('invalid login')

    gateway      = _init_processor()[0]
    logging.debug(str(gateway))
    
    # pick all files that are send in this API
    # support sending multiple files in a single request
    for key, the_file in request.FILES.iteritems():
        the_file = the_file[0]
        content_type = the_file.content_type
        
        if content_type == 'application/octet-stream':
            content_type = guess_mime_type(the_file.name)
            
        asset_class  = models.manager(models.AssetClass).get(name = models.AssetClass.UPLOAD)
    
        if not asset_class.has_consumers(content_type):
            raise ValidationError(
                'Unsupported content type: %s' % content_type)
    
        upload = operations.create_asset_from_stream(
            data_stream = StringIO(the_file.read()),
            owner       = request.user,
            producer    = gateway,
            asset_class = models.AssetClass.UPLOAD,
            file_name   = the_file.name,
            mime_type  = content_type)
    
        operations.publish_work_item(upload)
    
    return {
        'status'   : 202,
        # 'location' : upload.get_absolute_url(),
        }

##############################################################################
@login_required
@json_view
def split_document(request):
    """
    Create a new document from the given existing document, starting from the
    page given.  This is a "split" document operation.

    """
    page_view_name = request.GET.get('view_name', DEFAULT_PAGE_VIEW_NAME)
    old_document = request.user.documents.get(pk = int(request['id']))
    new_document = operations.split_document(
        old_document,
        int( request['split_after_page'] ))

    # TODO: what work items are generated by spliting a document?

    return {
        'original-document' : document_as_json_dict(old_document, page_view_name),
        'new_docment'       : document_as_json_dict(new_document, page_view_name),
        }

##############################################################################
@login_required
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

    # TODO: what work items are generated by merging two documents?

    return {
        'document' : document_as_json_dict(refreshed(target)),
        }

##############################################################################

@json_view
def get_document_info(request, pk):
    """
    Get a JSON representation of document.

    """
    document = request.user.documents.get(pk = pk)
    page_view_name = request.GET.get('view_name', DEFAULT_PAGE_VIEW_NAME)

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
    
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = \
        'attachment; filename=doc-%d.pdf' % document.pk
    pdf.render_document(document, response, request.user.username, str(document.pk))

    return response

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

    if request.has_key('title'):
        document.title = request['title']
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
    request.user.document.get(pk = pk).delete()

    # TODO: clean up stuff related to the document

    return {}

##############################################################################

@json_view
def get_page_info(request, pk):
    """
    Retrieve a page

    """
    view_name = request.GET.get('view_name', 'image')
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

    return HttpResponseRedirect(
        s3.generate_url(
            page.assets.get(asset_class__name = view_name).s3_key,
            expires_in = settings.S3_ACCESS_WINDOW ))

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
    show_count = param_is_true(request.GET.get('doc_count', 'false'))
    show_url   = param_is_true(request.GET.get('url', 'false'))

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

##############################################################################

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
        show_url       = param_is_true(request.GET.get('show_url', 'false')))


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
    start_index  = int(request.GET.get('start_index', 0))
    num_rows     = int(request.GET.get('num_rows', 250))
    page_view_name = request.GET.get('view_name', DEFAULT_PAGE_VIEW_NAME)
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
        



    