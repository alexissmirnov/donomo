from __future__ import with_statement
import unittest
import traceback
import tempfile
from donomo.archive import models, operations
import os
from cStringIO import StringIO

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]

def function():
    """
    Get the name of the current function
    """
    return traceback.extract_stack(limit=1)[0][2]

class DocumentOperations(unittest.TestCase):
# pylint: disable-msg=E1101
    """
    Validate the various doucment related operations.
    """

    test_data = 'This is just a test'

    def setUp(self):
        """
        Setup steps before running any tests
        """
        try:
            self.user = models.User.objects.get(username = 'testuser' )
        except models.User.DoesNotExist:
            # Make sure we have a test user
            self.user = models.User.objects.create_user(
                username = 'testuser',
                email    = 'testuser@donomo.com',
                password = models.User.objects.make_random_password())

        self.processor = operations.get_or_create_processor(
            MODULE_NAME,
            [])[0]

    def test_001_user_created(self):
        """
        Make sure setup worked - is there are user?

        """
        self.failIf(
            self.user is None,
            'User creation failed.')

    def test_002_create_processor(self):
        """
        Make sure setup worked - is there a processor?

        """
        self.failIf(
            self.processor is None,
            'Procesor not created properly')

    def test_003_create_upload_from_stream(self):
        """
        Create a new upload
        """

        upload = operations.create_upload_from_stream(
            self.processor,
            self.user,
            '%s.dat' % function(),
            StringIO('This is just a test'),
            'text/plain')

    def test_003_create_upload_from_file(self):
        """
        Create a new upload
        """

        fd, temp_file_name = tempfile.mkstemp()
        try:
            os.write(fd, self.test_data)
            os.close(fd)
            upload = operations.create_upload_from_file(
                self.processor,
                self.user,
                temp_file_name,
                'text/plain')
        finally:
            os.remove(temp_file_name)


