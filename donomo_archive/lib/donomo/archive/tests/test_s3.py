
# pylint: disable-msg=C0111
#  -> missing docstring

from cStringIO import StringIO
from donomo.archive.utils import s3
import os
import tempfile
import time
import unittest


class S3TestCase(unittest.TestCase):

    #-------------------------------------------------------------------------

    content       = "This is some test data that we'll play with\n"
    content_type  = 'text/plain'

    #-------------------------------------------------------------------------

    def _validate_and_remove_upload( self, s3_path ):

        time.sleep(2)

        self.assert_(s3.file_exists(s3_path) == True)

        temp_buffer = StringIO()
        meta_data = s3.download_to_stream(s3_path, temp_buffer)

        self.assert_( self.content_type == meta_data['Content-Type'] )
        self.assert_( len(self.content) == meta_data['Content-Length'] )
        self.assert_( self.content == temp_buffer.getvalue() )

        s3.delete_file(s3_path)
        time.sleep(2)

        self.assert_( s3.file_exists(s3_path) == False )

    #-------------------------------------------------------------------------

    def test_upload_from_stream(self):

        s3.initialize()

        s3_path = 'test-directory/test_002_upload_from_stream.txt'

        s3.upload_from_stream(
            s3_path,
            StringIO(self.content),
            self.content_type )

        self._validate_and_remove_upload( s3_path )

    #-------------------------------------------------------------------------

    def test_upload_from_file(self):

        s3.initialize()

        s3_path = 'test-directory/test_002_upload_from_file.txt'

        file_descriptor, local_path = tempfile.mkstemp(suffix='.txt')
        try:
            try:
                os.write(file_descriptor, self.content)
            finally:
                os.close(file_descriptor)

            s3.upload_from_file(
                s3_path,
                local_path,
                self.content_type)
        finally:
            os.remove(local_path)

        self._validate_and_remove_upload( s3_path )

    #-------------------------------------------------------------------------


