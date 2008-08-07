"""
Full Text Indexer Process Driver
"""

from __future__             import with_statement
from donomo.archive.service import ProcessDriver
from donomo.archive.models  import Page, manager
from django.conf            import settings
from django.template        import Template, Context
from django.core.validators import ValidationError
from logging                import getLogger
from StringIO               import StringIO
import httplib2
import simplejson
import urllib
import os

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]

logging = getLogger(MODULE_NAME)

# ----------------------------------------------------------------------------

def get_driver():

    """ Factory function to retrieve the driver object implemented by this
        this module
    """

    return IndexDriver()

# ----------------------------------------------------------------------------

class IndexDriver(ProcessDriver):

    """ Full Text Indexer Process Driver
    """

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    SERVICE_NAME = MODULE_NAME

    DEFAULT_OUTPUTS = []

    ACCEPTED_CONTENT_TYPES = [ 'text/plain' ]

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

    SOLR_UPDATE_URL = 'http://%s/solr/update/' % settings.SOLR_HOST

    SOLR_QUERY_URL = 'http://%s/solr/select/' % settings.SOLR_HOST

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def handle_work_item(self, item):

        """ Process a work item.  The work item will be provided and
            its local temp file will be cleaned up by the process driver
            framework.  If this method returns true, the work item will
            also be removed from the work queue.
        """

        return self.index_page_from_file(
            item['Object'].page,
            item['Local-Path'] )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    @staticmethod
    def get_ocr_text( original_text ):
        """ Get a version of the OCR text that the indexer can handle
            Omit all non-ascii characters from the input.
        """

        # TODO: Must we omit non-ascii chars from the index input?

        return "".join(
            [ char
              for char in original_text
              if ord(char) < 128 ] )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def index_page_from_string( self, page, text ):
        """
        Update the full-text index for the given page.  The textual
        content of the page the string 'text'.

        """
        http_client = httplib2.Http()

        data = {
            'page' : page,
            'text' : self.get_ocr_text(text),
            }

        response, content = http_client.request(
            uri     = self.SOLR_UPDATE_URL,
            method  = 'POST',
            body    = self.SOLR_UPDATE_TEMPLATE.render(Context(data)),
            headers = { "Content-type" : "text/xml; charset=utf-8" })

        if response.status >= 400:
            logging.error(
                'Failed to index page (%s, %s)' % (
                    response.status,
                    content ))
            return False

        logging.info('Updated full-text index for %s' % page)

        return True

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def index_page_from_file(self, page, text_file_path):
        """
        Update the full-text index for the given page.  The textual
        content of the page is in the file referenced by file_path.

        """
        with open(text_file_path, 'r') as text_file:
            return self.index_page_from_string(page, text_file.read())

# ----------------------------------------------------------------------------

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

# ----------------------------------------------------------------------------

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
        IndexDriver.SOLR_QUERY_URL,
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


# ----------------------------------------------------------------------------

def collate_results( query_results ):
    """
    Transform a SOLR response (dictionary parsed from JSON) into a dictionary
    more directly suitable for our purposes.  Pages are indexed individually
    but we want to collate them into documents and store any highlighting
    information alongside the document.

    The resulting dictionary has the following structure.

    documents = {
        document.pk : {
            solr_label_x     : solr_value_x,
            'document_model' : document_model,
            'search_hits'    : {
                position : {
                    'page_model'   : page_model,
                    'highlighting' : {
                        field : [ snippet1, snippet2 ],
                    },
                }
            }
        }
    }

    """
    documents = {}

    for page_result in query_results['response']['docs']:

        #
        # Find the page in the database
        #

        page_id = page_result['id']
        page_model = manager(Page).get(pk = page_id)

        #
        # Get or create an entry for this pages document
        #

        document = documents.setdefault(
            page_model.document.pk,
            { 'document_model' : page_model.document,
              'search_hits'    : {},
              })

        #
        # take the SOLR search result and merge in the page model and
        # highlighting information
        #

        page_result.update(
            page_model   = page_model,
            highlighting = query_results['highlighting'][page_id] )

        #
        # Save the resulting merged result as a hit or this document
        #

        document['search_hits'][ page_model.position ] = page_result


    return documents

# ----------------------------------------------------------------------------

def query( user, query_string, start_index = 0, num_rows = 50):
    """
    Query the SOLR index on behalf of the user and return the collated results

    """
    return {
        'query'       : query_string,
        'start_index' : start_index,
        'max_rows'    : num_rows,
        'documents'   : collate_results( user,
                                         raw_query( user,
                                                    query_string,
                                                    start_index,
                                                    num_rows ) ),
        }

# ----------------------------------------------------------------------------

def reset():
    """
    Delete the entire index
    """
    logging.critical('Deleting search index')

    http_client = httplib2.Http()
    response, content = http_client.request(
        uri     = IndexDriver.SOLR_UPDATE_URL,
        method  = 'POST',
        body    = "<delete><query>*:*</query></delete><commit/>",
        headers = { "Content-Type" : "text/xml; charset=utf-8" } )

    if response.status != 200:
        message = 'Failed to delete search index:\n%s' % content
        logging.error(message)
        raise Exception(message)

    logging.critical('Search index deleted')

# ----------------------------------------------------------------------------
