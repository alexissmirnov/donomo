"""
Full Text Indexer Process Driver
"""

from donomo.archive.service import ProcessDriver
from django.conf            import settings
from django.template.loader import render_to_string
from logging                import getLogger
from httplib2               import Http
import simplejson

logging = getLogger('indexer')

# ---------------------------------------------------------------------------

def get_driver():

    """ Factory function to retrieve the driver object implemented by this
        this module
    """

    return IndexDriver()

# ---------------------------------------------------------------------------

class IndexDriver(ProcessDriver):

    """ Full Text Indexer Process Driver
    """

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    SERVICE_NAME = 'Index'

    DEFAULT_OUTPUTS = []

    ACCEPTED_CONTENT_TYPES = [ 'text/plain' ]

    SOLR_UPDATE_TEMPLATE = 'services/solr-document-update.xml'

    SOLR_UPDATE_URL = 'http://%s/solr/update/' % settings.SOLR_HOST

    SOLR_QUERY_URL = 'http://%s/solr/select/' % settings.SOLR_HOST

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def handle_work_item(self, item):

        """ Process a work item.  The work item will be provided and
            its local temp file will be cleaned up by the process driver
            framework.  If this method returns true, the work item will
            also be removed from the work queue.
        """

        return self.index_page(
            item['Object'].page,
            item['Local-Path'] )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    @staticmethod
    def get_ocr_text( ocr_output_path):
        """ Get a version of the OCR text that the indexer can handle
            Omit all non-ascii characters from the input.

            TODO: Can we do better than this?
        """

        from __future__ import with_statement

        with open(ocr_output_path, 'r') as ocr_output_file:
            text = "".join(
                [ char for char in ocr_output_file.read()
                  if ord(char) < 128 ] )

        return text

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def index_page(self, page, ocr_output_path):

        """ Update the full-text index for the given page.  The textual
            content of the page is in the file referencec by ocr_output_path
        """

        http_client = Http()

        body = render_to_string(
            self.SOLR_UPDATE_TEMPLATE,
            { 'page' : page,
              'text' : self.get_ocr_text(ocr_output_path),
              } )

        response, content = http_client.request(
            uri     = self.SOLR_UPDATE_URL,
            method  = 'POST',
            body    = body,
            headers = { "Content-type" : "text/xml; charset=utf-8" })

        if response.status >= 400:
            logging.error(
                'Failed to index page (%s, %s)' % (
                    response.status,
                    content ))
            return False

        response, content = http_client.request(
            uri     = self.SOLR_UPDATE_URL,
            method  = 'POST',
            body    = "<commit/>",
            headers = { "Content-type" : "text/xml; charset=utf-8" })

        if response.status >= 400:
            logging.error(
                'Failed to commit ==index' % (
                    response.status,
                    content ))
            return False

        logging.info('Updated full-text index for %s' % page)

        return True

# ---------------------------------------------------------------------------

def query( user, query_string, start_index = 0, num_rows = 10):

    solr_query_params = {
        'q' : 'owner:%d AND %s' % (user.id, query_string),
        'version' : 2.2,
        'start'   : start_index,
        'rows'    : num_rows,
        'indent'  : 'on',
        'hl'      : 'true',
        'wt'      : 'json',
        }

    solr_query_string = urllib.urlencode(solr_query_params)

    solr_request_url = '%s?%s' % (
        IndexDriver.SOLR_QUERY_URL,
        solr_query_string)

    log.debug('search query is %s' % solr_query_string)

    response, content = httplib2.Http().request( solr_request_url, 'GET' )

    logging.debug('GET to %s returns %s\n%s' % (request_url, res, content))

    if ressponse.status != 200:
        raise Exception("Search query failed")

    return simplejson.load(content)

# ---------------------------------------------------------------------------
