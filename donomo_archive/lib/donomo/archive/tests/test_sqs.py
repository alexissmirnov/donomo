
# pylint: disable-msg=C0111
#  -> missing docstring

from donomo.archive.utils import sqs
from unittest import TestCase

class SQS(TestCase):

    # ------------------------------------------------------------------------

    def test_post_message(self):

        sqs.clear_all_messages()

        received = sqs.get_message( max_wait_time = 10)

        self.assert_( received is None, 'Queue should be empty' )

        original = { 'body' : r'This is a test message\nWith two lines\n' }

        sqs.post_message( original )

        received = sqs.get_message( max_wait_time = 10, visibility_timeout = 5 )

        self.assert_( received is not None )
        self.assert_( received['body'] == original['body'] )

        sqs.delete_message(received)

        self.assert_( sqs.get_message( max_wait_time = 15 ) is None )

    # ------------------------------------------------------------------------
