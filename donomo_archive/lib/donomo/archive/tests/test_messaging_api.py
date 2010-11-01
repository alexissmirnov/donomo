from django.test.client import Client
from django.test.utils import setup_test_environment
from donomo.archive           import operations
from donomo.archive.models import *
from donomo.archive.service import mail_parser
from donomo.archive.utils import sqs
import os
import unittest2 as unittest
import json
import time
import datetime


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
            work_item = operations.retrieve_work_item(max_wait_time = 3)
            if work_item:
                mail_parser.handle_work_item(self.processor, work_item)
                operations.close_work_item(work_item, True)
            else:
                logging.info('no more work items')
                break
            
    def setUp(self):
        self._init_infra();
        self.user, self.password = self._init_user();
        self.processor = self._init_processor();
        self.message_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.client = Client()
        self.client.login(username = self.user.username, password = self.password)


    def tearDown(self):
        sqs.clear_all_messages()
        User.objects.all().delete()
    
    # ------------------------------------------------------------------------

    def test_init(self):
        self.assert_( self.user is not None )
        self.assert_( self.processor is not None )

    def test_get_message_api(self):
        MessageAggregate.objects.all().delete()
        Message.objects.all().delete()
        MessageRule.objects.all().delete()
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message1.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        time.sleep(2)
        self._process_queue();

        response = self.client.login(username = self.user.username, password = self.password)
        self.assertEqual(response, True)
        response = self.client.get('/api/1.0/sync/events/')
        self.assertEqual(response.status_code, 200)

        body = json.loads(response.content)
        self.assertEqual(body['status'], 200)
        self.assertEqual(len(body['aggregates']), 1)
        
    def test_get_modified_since(self):
        """
        Checks that modified_since follows the the order of message processing
        """
        MessageAggregate.objects.all().delete()
        Message.objects.all().delete()
        MessageRule.objects.all().delete()
        
        # add 2 messages
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message1.eml'), 'testuser@donomo.com', 'label3', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message1.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        time.sleep(1)
        self._process_queue();
        
        # check we have 2 messages
        self.assertEqual(Message.objects.all().count(), 2)

        # take the time
        now = datetime.datetime.utcnow()
        ms_time_before_equeuing = time.mktime(now.timetuple())*1000000+now.microsecond
        
        # add one more message
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message2.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        time.sleep(1)
        self._process_queue();

        # now there's 2 messages in 1 conversation
        self.assertEqual(Message.objects.all().count(), 3)

        # send an API request to get message modified after ms_time_before_equeuing
        response = self.client.get('/api/1.0/sync/events/?body=0&modified_since=%.0f' % ms_time_before_equeuing)
        self.assertEqual(response.status_code, 200)

        # since the 3rd message belonged to the same conversation as the 2nd message,
        # both messages should have been modified
        body = json.loads(response.content)
        self.assertEqual(body['status'], 200)
        self.assertEqual(len(body['messages']), 2)

        # get the last modified timestamp of the last message
        date_timestamp = datetime.datetime.fromtimestamp(float(body['messages'][1]['modified_date'])/1000000)

        # There should not be anything fresher then the last entry in the response
        self.assertEqual(Message.objects.filter(status = Message.STATUS_READY, modified_date__gt = date_timestamp).count(), 0)
        
        # Send the request with the lasted modified timestamp
        response = self.client.get('/api/1.0/sync/events/?body=0&modified_since=%s' % body['messages'][1]['modified_date'])
        
        body = json.loads(response.content)
        self.assertEqual(body['status'], 200)
        
        # The request returns nothing since there are no fresher messages
        self.assertEqual(len(body['messages']), 0)


    def test_get_newsletter(self):
        """
        Checks that modified_date is set on all messages that are moved into a newsletter aggregate
        """
        MessageAggregate.objects.all().delete()
        Message.objects.all().delete()
        MessageRule.objects.all().delete()

        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message1.eml'), 'testuser@donomo.com', 'label4', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message2.eml'), 'testuser@donomo.com', 'label4', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message3.eml'), 'testuser@donomo.com', 'label4', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message4.eml'), 'testuser@donomo.com', 'label4', 'S,F')
        self._process_queue();

        # now there's 4 messages, but one of them isn't part of the newsletter aggregate
        self.assertEqual(Message.objects.all().count(), 4)

        time_after_processing_before_newsletter = datetime.datetime.now()
                
        # take the time
        now = datetime.datetime.utcnow()
        ms_time_before_rule = time.mktime(now.timetuple())*1000000+now.microsecond

        # add a newsletter rule for the sender
        new_conversation = MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, owner = self.user, tags__label = 'label4')[0]
        rule = MessageRule(type = MessageRule.NEWSLETTER, owner = self.user, sender_address = new_conversation.messages.all()[0].sender_address)
        rule.save()
        operations.apply_message_rule(rule)
        
        response = self.client.get('/api/1.0/sync/events/?body=0&modified_since=%.0f' % ms_time_before_rule)
        self.assertEqual(response.status_code, 200)
        
        body = json.loads(response.content)
        
        # The request returns nothing since there are no fresher messages
        self.assertEqual(len(body['messages']), 3)
        

# ----------------------------------------------------------------------------

if __name__ == '__main__':
    setup_test_environment()
    unittest.main()
