"""
Full Text Indexer Process Driver
"""

from __future__             import with_statement
from donomo.archive.models  import AssetClass, MimeType
from donomo.archive.utils   import misc
from django.conf            import settings
from django.template        import Template, Context
from django.core.validators import ValidationError
from StringIO               import StringIO
import httplib2
import simplejson
import urllib
import os
import logging

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]

logging = logging.getLogger(MODULE_NAME)

DEFAULT_INPUTS  = (
    AssetClass.PAGE_TEXT,
    )

DEFAULT_OUTPUTS = ()

DEFAULT_ACCEPTED_MIME_TYPES = (
    MimeType.TEXT,
    MimeType.HTML,
    )

SOLR_UPDATE_TEMPLATE = Template(
    """{% spaceless %}
       {% autoescape on %}
       <?xml version="1.0" encoding="UTF-8"?>
       <add>
         <doc>
           <field name="page_id">{{id}}</field>
           <field name="did">{{did}}</field>
           <field name="text">{{content}}</field>
           <field name="owner">{{owner.id}}</field>{% for tag in tags %}
           <field name="tag">{{tag}}</field>{% endfor %}
         </doc>
       </add>
       <commit/>
       {% endautoescape %}
       {% endspaceless %}""")

SOLR_UPDATE_URL = 'http://%s/solr/update/?commit=true' % settings.SOLR_HOST

SOLR_QUERY_URL = 'http://%s/solr/select/' % settings.SOLR_HOST

##############################################################################

def handle_work_item(processor, item):

    """ Process a work item.  The work item will be provided and its local
        temp file will be cleaned up by the process driver framework.
        If this method returns true, the work item will also be
        removed from the work queue.

    """

    _index_page_from_file(
        item['Asset-Instance'].related_page,
        item['Local-Path'] )

##############################################################################

def _index_page_from_file(page, local_path ):
    """
    Update the full-text index for the given page.  The textual
    content of the page is in the file referenced by file_path.

    """
    with open(local_path, 'r') as text_file:
        _index_page_from_string(page, text_file.read())

##############################################################################

def _index_page_from_string( page, text ):
    """
    Update the full-text index for the given page.  The textual
    content of the page the string 'text'.

    """
    http_client = httplib2.Http()

    text = misc.extract_text_from_html(text) 

    data = {
        'id' : page.pk,
        'content' : text,
        'did' : page.document.pk,
        'owner': page.owner,
        'tags':page.document.tags.all()
        }

    body = SOLR_UPDATE_TEMPLATE.render(Context(data))
    logging.debug('Sending to SOLR:')
    logging.debug('--------------')
    logging.debug(body)
    logging.debug('--------------')

    response, content = http_client.request(
        uri     = SOLR_UPDATE_URL,
        method  = 'POST',
        body    = body,
        headers = { "Content-type" : "text/xml; charset=utf-8" })

    if response.status >= 400:
        raise Exception(
            'Failed to index page (%s, %s)' % (
                response.status,
                content ))

    logging.info('Updated full-text index for %s' % page)


###############################################################################

def validate_query_string(query_string):
    """
    Make sure parentheses in query string are properly balanced and that they
    don't try to escape any parentheses we've added around the expression.
    For example:

       query_string = 'blah) OR (OWNER:foo'

    """
    nesting_level = 0
    for char in query_string:
        if char == '(':
            nesting_level += 1
        elif char == ')':
            nesting_level -= 1
            if nesting_level < 0:
                raise ValidationError("Malformed query string")
    if nesting_level != 0:
        raise ValidationError("Malformed query string")

###############################################################################

def raw_query( user, query_string, start_index = 0, num_rows = 50):
    """
    Query the SOLR index on behalf of the user and return the raw results

    """
    validate_query_string(query_string)
    solr_query_params = {
        'q'            : 'owner:%d AND (%s)' % (user.id, query_string),
        'version'      : 2.2,
        'start'        : start_index,
        'rows'         : num_rows,
        'indent'       : 'on',
        'hl'           : 'true',
        'hl.fl'        : 'tags,text',
        'hl.snippets'  : 3,
        'wt'           : 'json',
        }

    solr_query_string = urllib.urlencode(solr_query_params)

    solr_request_url = '%s?%s' % (
        SOLR_QUERY_URL,
        solr_query_string)

    logging.debug(
        'search query is %s' % solr_query_string)

    response, content = httplib2.Http().request( solr_request_url, 'GET' )

    logging.debug(
        'GET to %s returns %s\n%s' % (
            solr_request_url,
            response,
            content ))

    if response.status != 200:
        raise Exception("Search query failed")

    return simplejson.load(StringIO(content))

###############################################################################

def query( user,
           query_string,
           start_index = 0,
           num_rows = 50):
    """
    Query the SOLR index on behalf of the user and return results
    """
    res = raw_query( user,
                    query_string,
                    start_index,
                    num_rows )['response']

    return {
        'query'       : query_string,
        'start_index' : start_index,
        'max_rows'    : num_rows,
        'results'     : res,
        }

###############################################################################

def reset():
    """
    Delete the entire index
    """
    logging.critical('Deleting search index')

    http_client = httplib2.Http()
    response, content = http_client.request(
        uri     = SOLR_UPDATE_URL,
        method  = 'POST',
        body    = "<delete><query>*:*</query></delete><commit/>",
        headers = { "Content-Type" : "text/xml; charset=utf-8" } )

    if response.status != 200:
        message = 'Failed to delete search index:\n%s' % content
        logging.error(message)
        raise Exception(message)

    logging.critical('Search index deleted')

###############################################################################
