from django.test.client import Client
from django.test.utils import setup_test_environment
from donomo.archive           import operations
from donomo.archive.models import *
from donomo.archive.service import mail_parser
from donomo.archive.utils import sqs
import os
import unittest2 as unittest

# ----------------------------------------------------------------------------

class TestMessagingApi(unittest.TestCase):
    """
    """
    user = None
    processor = None
    password = None
    
    # ------------------------------------------------------------------------

    @staticmethod
    def _init_infra():

        operations.initialize_infrastructure()
        sqs.clear_all_messages()

    # ------------------------------------------------------------------------
    @staticmethod
    def _init_user():
        password = manager(User).make_random_password()
        return manager(User).create_user(
                username = 'testuser',
                email    = 'testuser@donomo.com',
                password = password), password
            

    def _init_processor(self):
        MODULE_NAME     = 'mail_parser'
        
        DEFAULT_INPUTS  = [ AssetClass.UPLOAD ]
        DEFAULT_OUTPUTS = [ AssetClass.MESSAGE_PART ]
        DEFAULT_ACCEPTED_MIME_TYPES = [ MimeType.MAIL ]
    
        return operations.initialize_processor(
            MODULE_NAME,
            DEFAULT_INPUTS,
            DEFAULT_OUTPUTS,
            DEFAULT_ACCEPTED_MIME_TYPES ) [0]
        
    def _enqueue_message(self, message_file, accountname, label, flags):
        new_item = operations.create_asset_from_file(
            file_name    = message_file,
            owner        = self.user,
            producer     = self.processor,
            asset_class  = AssetClass.UPLOAD,
            child_number = 0,
            mime_type    = MimeType.MAIL )
        new_item.orig_file_name += ',ACCOUNT=%s' % accountname
        new_item.orig_file_name += ',LABEL=%s' % label
        new_item.orig_file_name += ',FLAGS='
        for f in flags:
            new_item.orig_file_name += ',' + f
        new_item.save()
        operations.publish_work_item(new_item)

    def _process_queue(self):
        while True:
            work_item = operations.retrieve_work_item(max_wait_time = 1)
            if work_item:
                mail_parser.handle_work_item(self.processor, work_item)
                operations.close_work_item(work_item, True)
            else:
                break
            
    def setUp(self):
        self._init_infra();
        self.user, self.password = self._init_user();
        self.processor = self._init_processor();
        self.message_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.client = Client()
    
    def tearDown(self):
        sqs.clear_all_messages()
        User.objects.all().delete()
    
    # ------------------------------------------------------------------------

    def test_init(self):
        self.assert_( self.user is not None )
        self.assert_( self.processor is not None )

    def test_get_api(self):
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message3.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message2.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message1.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        self._process_queue();

        response = self.client.login(username = self.user.username, password = self.password)
        self.assertEqual(response, True)
        response = self.client.post('/account/login/', {'username': self.user.username, 'password': self.password})
        response = self.client.get('/api/1.0/messages/', **{'user':self.user})
        self.assertEqual(response.status_code, 200)
        



# ----------------------------------------------------------------------------

if __name__ == '__main__':
    setup_test_environment()
    unittest.main()
