#!/usr/bin/env python
"""
Test cases for docstore.core.utils
"""

from __future__ import with_statement
from cStringIO import StringIO
from donomo.archive.utils import s3, sqs
from time import sleep
import os
import tempfile
import traceback
import unittest

# ----------------------------------------------------------------------------

def function():
    """
    Get the name of the current function
    """
    return traceback.extract_stack(limit=1)[0][2]

# ----------------------------------------------------------------------------

class S3(unittest.TestCase):
    """
    S3 Tests
    """

    BUCKET_NAME    = "unittest.donomo.com"
    temp_file_name = None
    file_data      = "This is some test data that we'll play with\n"

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def setUp(self):
        """
        Called before each test
        """

        self.temp_file_name = None

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def tearDown(self):
        """
        Called after each test
        """

        if self.temp_file_name:
            os.system('rm -f %s' % self.temp_file_name)
            self.temp_file_name = None

        sleep(2)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def test_001_create_s3_bucket(self):
        """
        Create an S3 bucket
        """

        bucket = s3.get_bucket(self.BUCKET_NAME, create=True)
        self.assertNotEqual(None, bucket)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def test_002_get_s3_bucket(self):
        """
        Retrieve an S3 bucket
        """

        bucket = s3.get_bucket(self.BUCKET_NAME)
        self.assertNotEqual(None, bucket)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    def validate_and_remove_uploaded_file(
        self,
        bucket,
        s3_path,
        content_type,
        content):
        """
        """

        sleep(2)
        self.failUnless(
            s3.key_exists(
                bucket,
                s3_path),
            "File should exist now")

        temp_file = StringIO()

        meta_data = s3.download_stream(
            bucket,
            s3_path,
            temp_file)

        self.assertEqual(
            meta_data['Content-Type'],
            content_type,
            "Content type doesn't match")

        self.assertEqual(
            meta_data['Content-Length'],
            len(content),
            "Size doesn't match")

        self.assertEqual(
            temp_file.getvalue(),
            content,
            "Data doesn't match")

        s3.delete_file(
            bucket,
            s3_path)

        sleep(2)

        self.failIf(
            s3.key_exists( bucket, s3_path),
            "File should have been deleted")

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def test_003_stream_upload(self):
        """
        Upload a file to a a bucket
        """

        s3_path = 'test-directory/%s.txt' % function()
        bucket = s3.get_bucket(self.BUCKET_NAME)

        s3.upload_stream(
            bucket,
            s3_path,
            StringIO(self.file_data),
            'text/plain')

        self.validate_and_remove_uploaded_file(
            bucket,
            s3_path,
            'text/plain',
            self.file_data)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def test_004_file_upload(self):
        """
        Upload a file to a a bucket
        """

        s3_path = 'test-directory/%s.txt' % function()
        bucket = s3.get_bucket(self.BUCKET_NAME)

        fd, local_path = tempfile.mkstemp(suffix='.txt')
        try:
            os.write(fd, self.file_data)
            os.close(fd)

            s3.upload_file(
                bucket,
                s3_path,
                local_path )
        finally:
            os.remove(local_path)

        self.validate_and_remove_uploaded_file(
            bucket,
            s3_path,
            'text/plain',
            self.file_data)



# ----------------------------------------------------------------------------

class SQS(unittest.TestCase):
    """
    SQS Tests
    """

    MESSAGE_BODY = r'This is a test message\nWith two lines\n'
    QUEUE_NAME   = "test_queue"

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def setUp(self):
        """
        Clear the sqs queue.
        """
        queue = sqs.get_queue(self.QUEUE_NAME, create = True)
        for message in sqs.get_message_iter(queue, poll_frequency = 1, max_wait_time = 2):
            message.delete()

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def test_001_get_queue(self):
        """
        Get an SQS Queue
        """

        queue = sqs.get_queue(self.QUEUE_NAME)
        self.assertNotEqual(None, queue)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def test_002_post_message(self):
        """
        Put a message into a queue
        """
        queue = sqs.get_queue(self.QUEUE_NAME)
        sqs.post_message(
            queue,
            { 'body' : self.MESSAGE_BODY } )

        message = sqs.get_message(
            queue,
            poll_frequency = 1,
            max_wait_time  = 30)

        #print message._dict

        self.assertNotEqual(
            message,
            None,
            "Didn't receive a message")

        self.assertEqual(
            message['body'],
            self.MESSAGE_BODY,
            "Received the wrong message")

        sqs.delete_message(message)

# ----------------------------------------------------------------------------

def suite():
    """
    Return a test suite for this module
    """
    this_module = sys.modules[S3.__module__]
    return unittest.defaultTestLoader.loadTestsFromModule(this_module)


# =============================================================================

if __name__ == '__main__':
    unittest.main()


