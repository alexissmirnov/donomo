"""
Test Donomo Archive operations
"""

#
# pylint: disable-msg=C0103,C0111,R0904,W0401,W0614
#
#   C0103 - variables at module scope must be all caps
#   C0111 - missing docstring
#   R0904 - too many public methods
#   W0401 - wildcard import
#   W0614 - unused import from wildcard
#

from __future__ import with_statement
import unittest
import traceback
import tempfile
from donomo.archive.models import *
from donomo.archive import operations, models
from donomo.archive.service import pdf_generator
import os
from cStringIO import StringIO
from time import sleep
import datetime
import time


MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]

TEST_DATA = """
This is just a test!
In the event of actual data, there would be something interesting here.
"""

class DocumentOperations(unittest.TestCase):


    # ------------------------------------------------------------------------

    @staticmethod
    def _init_user():
        try:
            return manager(User).get(username = 'testuser' )
        except User.DoesNotExist:
            # Make sure we have a test user
            return manager(User).create_user(
                username = 'testuser',
                email    = 'testuser@donomo.com',
                password = manager(User).make_random_password())

    # ------------------------------------------------------------------------

    @staticmethod
    def _init_producer():
        return operations.initialize_processor(
            name                        = MODULE_NAME + '_producer',
            default_inputs              = [],
            default_outputs             = [ AssetClass.DOCUMENT, 'test_data' ],
            default_accepted_mime_types = [] )

    # ------------------------------------------------------------------------

    @staticmethod
    def _init_consumer():
        return operations.initialize_processor(
            name                        = MODULE_NAME + '_consumer',
            default_inputs              = [AssetClass.DOCUMENT, 'test_data'],
            default_outputs             = [],
            default_accepted_mime_types = [ MimeType.TEXT, MimeType.BINARY ] )

    # ------------------------------------------------------------------------

    @staticmethod
    def _init_infra():
        from donomo.archive.utils import sqs

        operations.initialize_infrastructure()
        sqs.clear_all_messages()

    # ------------------------------------------------------------------------

    def _validate_consumer(self, asset, content):

        work_item = operations.retrieve_work_item(max_wait_time=30)

        self.assert_( work_item is not None )
        self.assert_( int(work_item['Asset-ID']) == asset.pk )
        self.assert_( open(work_item['Local-Path']).read() == content )

        operations.close_work_item(
            work_item         = work_item,
            delete_from_queue = True )

        work_item = operations.retrieve_work_item(max_wait_time=30)

        for i in work_item and work_item.iteritems() or ():
            print '  %s = %r' % i

        self.assert_( work_item is None )

    # ------------------------------------------------------------------------

    def setUp(self):
        self._init_infra()

        self.user = self._init_user()
        self.producer = self._init_producer() [0]
        self.consumer = self._init_consumer() [0]

    # ------------------------------------------------------------------------

    def tearDown(self):
        models.Process.objects.get(name = MODULE_NAME + '_producer').delete()
        models.Process.objects.get(name = MODULE_NAME + '_consumer').delete()
        models.AssetClass.objects.get(name = 'test_data').delete()


    # ------------------------------------------------------------------------

    def test_create_infra(self):
        from donomo.archive.utils import s3, sqs

        self.assert_(sqs._get_queue() is not None)
        self.assert_(s3._get_bucket() is not None)

    # ------------------------------------------------------------------------

    def test_create_user(self):
        self.assert_( self.user is not None )

    # ------------------------------------------------------------------------

    def test_create_producer(self):
        self.assert_( self.producer is not None )
        self.assert_( self._init_producer() [1] == False )

    # ------------------------------------------------------------------------

    def test_create_consumer(self):
        self.assert_( self.consumer is not None )
        self.assert_( self._init_consumer() [1] == False )

    # ------------------------------------------------------------------------

    def test_create_asset_from_stream(self):
        asset = operations.create_asset_from_stream(
            owner        = self.user,
            producer     = self.producer,
            asset_class  = 'test_data',
            data_stream  = StringIO(TEST_DATA),
            file_name    = 'create_asset_from_string.txt',
            child_number = 0,
            mime_type    = 'text/plain' )

        self.assert_( asset is not None )

        operations.publish_work_item(asset)

        self._validate_consumer(asset, TEST_DATA)

    # ------------------------------------------------------------------------

    def test_create_asset_from_file(self):
        fd, temp_file_name = tempfile.mkstemp()
        try:
            os.write(fd, TEST_DATA)
            os.close(fd)
            fd = None
            asset = operations.create_asset_from_file(
                owner        = self.user,
                producer     = self.producer,
                asset_class  = 'test_data',
                file_name    = temp_file_name,
                child_number = 0,
                mime_type    = 'text/plain' )

            self.assert_( asset is not None )

        finally:
            if fd is not None:
                os.close(fd)
            os.remove(temp_file_name)

        operations.publish_work_item(asset)

        self._validate_consumer(asset, TEST_DATA)

    # ------------------------------------------------------------------------

    def test_split_document(self):
        doc1 = operations.create_document( owner = self.user )

        pages = [ operations.create_page(doc1) for _ in xrange(10) ]

        self.assert_( doc1.num_pages == 10 )

        doc2 = operations.split_document(doc1, 5)

        self.assert_( doc1.num_pages == 5 )
        self.assert_( doc2.num_pages == 5 )

        for i in xrange(5):
            self.assert_(pages[i].pk   == doc1.pages.get(position=i+1).pk)
            self.assert_(pages[i+5].pk == doc2.pages.get(position=i+1).pk)

    # ------------------------------------------------------------------------

    def test_merge_documents_1(self):
        # Append doc2 to end of doc 1
        doc1 = operations.create_document( owner = self.user )
        doc2 = operations.create_document( owner = self.user )

        pages = ( [ operations.create_page(doc1) for _ in xrange(5) ]
                  + [ operations.create_page(doc2) for _ in xrange(5) ] )

        self.assert_( doc1.num_pages == 5 )
        self.assert_( doc2.num_pages == 5 )

        operations.merge_documents(doc1, doc2, 5)

        self.assert_( manager(Document).filter( pk = doc2.pk ).count() == 0 )
        self.assert_( doc1.num_pages == 10 )

        for i in xrange(5):
            self.assert_(pages[i].pk   == doc1.pages.get(position=i+1).pk)
            self.assert_(pages[i+5].pk == doc1.pages.get(position=i+6).pk)

    # ------------------------------------------------------------------------


    def test_merge_documents_2(self):
        # Prepend doc2 to beginning of doc 1
        doc1 = operations.create_document( owner = self.user )
        doc2 = operations.create_document( owner = self.user )

        pages = ( [ operations.create_page(doc1) for _ in xrange(5) ]
                  + [ operations.create_page(doc2) for _ in xrange(5) ] )

        self.assert_( doc1.num_pages == 5 )
        self.assert_( doc2.num_pages == 5 )

        operations.merge_documents(doc1, doc2, 0)

        self.assert_( manager(Document).filter( pk = doc2.pk ).count() == 0 )
        self.assert_( doc1.num_pages == 10 )

        for i in xrange(5):
            self.assert_(pages[i].pk   == doc1.pages.get(position=i+6).pk)
            self.assert_(pages[i+5].pk == doc1.pages.get(position=i+1).pk)

    # ------------------------------------------------------------------------

    def test_merge_documents_3(self):
        # Insert doc2 into middle of doc 1
        doc1 = operations.create_document( owner = self.user )
        doc2 = operations.create_document( owner = self.user )

        pages = ( [ operations.create_page(doc1) for _ in xrange(5) ]
                  + [ operations.create_page(doc2) for _ in xrange(5) ] )

        self.assert_( doc1.num_pages == 5 )
        self.assert_( doc2.num_pages == 5 )

        operations.merge_documents(doc1, doc2, 3)

        self.assert_( manager(Document).filter( pk = doc2.pk ).count() == 0 )
        self.assert_( doc1.num_pages == 10 )

        # First 3 pages of doc1 stay first pages of 10 pager
        for i in xrange(0,3):
            self.assert_(pages[i].pk == doc1.pages.get(position=i+1).pk)

        # all pages from doc2 not starting at 4th page of 10 pager
        for i in xrange(3,8):
            self.assert_(pages[i+2].pk == doc1.pages.get(position=i+1).pk)

        # last tow pages of dooc 1 are now last two pages or 10 pager
        for i in xrange(8, 10):
            self.assert_(pages[i-5].pk == doc1.pages.get(position=i+1).pk)

    # ------------------------------------------------------------------------

    def test_tag_documents_by_time(self):
        # create an unclassified document
        doc0 = operations.tag_document( owner = self.user )

        asset0 = operations.create_asset_from_stream(
            owner        = self.user,
            producer     = self.producer,
            asset_class  = models.AssetClass.DOCUMENT,
            data_stream  = StringIO('some pdf'),
            file_name    = 'create_asset_from_string.txt',
            child_number = 1,
            related_document = doc0,
            mime_type        = models.MimeType.PDF )

        sleep(2)

        doc1 = operations.tag_document( owner = self.user )

        now = datetime.date.fromtimestamp(time.time())
        pdf_generator.classify_document(doc1, datetime.timedelta(0, 1))

        asset1 = operations.create_asset_from_stream(
            owner        = self.user,
            producer     = self.producer,
            asset_class  = models.AssetClass.DOCUMENT,
            data_stream  = StringIO('some pdf'),
            file_name    = 'create_asset_from_string.txt',
            child_number = 1,
            related_document = doc1,
            mime_type        = models.MimeType.PDF )

        # do we have a new tag?
        self.assert_( doc1.tags.all().count() == 1 )

        tag1 = doc1.tags.all()[0]

        self.assert_(tag1.tag_class == models.Tag.UPLOAD_AGGREGATE)

        # sleep 3 sec
        sleep(3)

        doc2 = operations.tag_document( owner = self.user )
        now = datetime.date.fromtimestamp(time.time())
        pdf_generator.classify_document(doc2, datetime.timedelta(0, 1))
        # is the second document tagged in the different tag?
        self.assert_( doc2.tags.all().count() == 1 )

        tag2 = doc2.tags.all()[0]

        self.assert_(tag2.label != tag1.label)

        asset2 = operations.create_asset_from_stream(
            owner        = self.user,
            producer     = self.producer,
            asset_class  = models.AssetClass.DOCUMENT,
            data_stream  = StringIO('some pdf'),
            file_name    = 'create_asset_from_string.txt',
            child_number = 1,
            related_document = doc2,
            mime_type        = models.MimeType.PDF )



        # sleep another 3 seconds and create the 3rd document,
        # but with a longer threshold
        sleep(3)

        doc3 = operations.tag_document( owner = self.user )
        now = datetime.date.fromtimestamp(time.time())
        pdf_generator.classify_document(doc3, datetime.timedelta(0, 10))

        # did this one got tagged with a same tag?
        self.assert_( doc2.tags.all().count() == 1 )
        self.assert_( tag2 == doc3.tags.all()[0] )

        asset3 = operations.create_asset_from_stream(
            owner        = self.user,
            producer     = self.producer,
            asset_class  = models.AssetClass.DOCUMENT,
            data_stream  = StringIO('some pdf'),
            file_name    = 'create_asset_from_string.txt',
            child_number = 1,
            related_document = doc3,
            mime_type        = models.MimeType.PDF )


