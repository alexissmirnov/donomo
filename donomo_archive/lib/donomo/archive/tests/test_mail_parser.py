import unittest2 as unittest
from donomo.archive.models import *
from donomo.archive.service import mail_parser
from donomo.archive           import operations
from django.test.utils import setup_test_environment
from donomo.archive.utils import sqs
import os
import time

# ----------------------------------------------------------------------------

class TestConversationNewsletter(unittest.TestCase):
    """
    """
    user = None
    processor = None
    
    # ------------------------------------------------------------------------

    @staticmethod
    def _init_infra():

        operations.initialize_infrastructure()
        sqs.clear_all_messages()

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
            work_item = operations.retrieve_work_item(max_wait_time = 5)
            if work_item:
                mail_parser.handle_work_item(self.processor, work_item)
                operations.close_work_item(work_item, True)
            else:
                break
            
    def setUp(self):
        self._init_infra();
        self.user = self._init_user();
        self.processor = self._init_processor();
        self.message_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    def tearDown(self):
        sqs.clear_all_messages()
    
    # ------------------------------------------------------------------------

    def test_init(self):
        self.assert_( self.user is not None )
        self.assert_( self.processor is not None )


    def test_simple_message(self):
        """
        Adding a message should produce 1 message object and 1 conversation
        """
        MessageAggregate.objects.all().delete()
        Message.objects.all().delete()
        MessageRule.objects.all().delete()
                 
        self._enqueue_message(os.path.join(self.message_dir, 'simple_message.eml'), 'testuser@donomo.com', 'label1', 'S,F')
        self._process_queue();
        
        self.assertEqual(Message.objects.all().count(), 1)
        self.assertEqual(MessageAggregate.objects.all().count(), 1)

    def test_conversation(self):        
        """
        3 messages in the same thread, added in reverse order. This means 'References' will be unresolved.
        Once all 2 are processed there should be 3 more messages and 1 more conversation.
        Also tests unicode of the subject line
        """
        original_message_count = Message.objects.all().count()
        original_aggregate_count = MessageAggregate.objects.all().count()
        
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message3.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message2.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'conversation_message1.eml'), 'testuser@donomo.com', 'label2', 'S,F')
        self._process_queue();
        
        self.assertEqual(Message.objects.all().count() - original_message_count, 3 )
        self.assertEqual(MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY).count() - original_aggregate_count, 1)
        
        new_conversation = MessageAggregate.objects.get(status = MessageAggregate.STATUS_READY, owner = self.user, tags__label = 'label2')
        
        self.assertEqual(new_conversation.creator.type, MessageRule.CONVERSATION)
        self.assertEqual(new_conversation.messages.all().count(), 3)

    def test_newsletter(self):
        """
        - receive a message (new conversation is created)
        - flag it as newsletter (conversation is replaced with a newsletter)
        - receive a message of the same type (they are all put in the newsletter)
        - forward one newsletter (that message ends up in a new conversation and still sits in the newsletter aggregate)
        - receive another newsletter
        """
        MessageAggregate.objects.all().delete()
        Message.objects.all().delete()
        MessageRule.objects.all().delete()

        original_message_count = Message.objects.all().count()
        original_conversation_count = MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.CONVERSATION).count()
        original_newsletter_count = MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.NEWSLETTER).count()

        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message1.eml'), 'testuser@donomo.com', 'label3', 'S,F')
        self._process_queue();

        # new conversation is created
        new_conversation = MessageAggregate.objects.get(owner = self.user, tags__label = 'label3')
        self.assertEqual(new_conversation.creator.type, MessageRule.CONVERSATION)
        self.assertEqual(MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.CONVERSATION).count(), original_conversation_count + 1)
        
        # another message arrives, another conversation created
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message2.eml'), 'testuser@donomo.com', 'label3', 'S,F')
        self._process_queue();

        # got two conversations
        self.assertEqual(MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.CONVERSATION).count(), original_conversation_count + 2)

        # add a newsletter rule for the sender
        rule = MessageRule(type = MessageRule.NEWSLETTER, owner = self.user, sender_address = new_conversation.messages.all()[0].sender_address)
        rule.save()
        operations.apply_message_rule(rule)
        
        # conversations got replaced by a newsletter
        self.assertEqual(MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.CONVERSATION).count(), original_conversation_count)
        self.assertEqual(MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.NEWSLETTER).count(), 1 + original_newsletter_count)
        
        # a newsletter was forwarded
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message3.eml'), 'testuser@donomo.com', 'label3', 'S,F')
        self._process_queue();

        # a new conversation is created
        self.assertEqual(MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.CONVERSATION).count(), 1 + original_conversation_count)
        
        # a new newsletter was received
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message4.eml'), 'testuser@donomo.com', 'label3', 'S,F')
        self._process_queue();
        
        # the new newsletter message goes into the existing aggregate
        # the conversation is still present, with 2 messages
        self.assertEqual(MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.NEWSLETTER).count(), 1 + original_newsletter_count)

        newsletter = MessageAggregate.objects.get(status = MessageAggregate.STATUS_READY, owner = self.user, creator__type = MessageRule.NEWSLETTER, tags__label = 'label3')
        self.assertEqual(newsletter.messages.all().count(), 3)

        conversation = MessageAggregate.objects.get(status = MessageAggregate.STATUS_READY, owner = self.user, creator__type = MessageRule.CONVERSATION, tags__label = 'label3')
        self.assertEqual(conversation.messages.all().count(), 2)

    def test_newsletter_delayed_rule_application(self):
        """
        - receive several messages from the same source (newsletter) and one message with a forward
        - apply a newsletter rule
        - check there's a single newsletter aggreate and a single conversation (for the forward)
        - check the names of conversation and newsletter
        """
        MessageAggregate.objects.all().delete()
        Message.objects.all().delete()
        MessageRule.objects.all().delete()
        
        original_message_count = Message.objects.all().count()
        original_conversation_count = MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.CONVERSATION).count()
        original_newsletter_count = MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, creator__type = MessageRule.NEWSLETTER).count()

        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message1.eml'), 'testuser@donomo.com', 'label4', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message2.eml'), 'testuser@donomo.com', 'label4', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message3.eml'), 'testuser@donomo.com', 'label4', 'S,F')
        self._enqueue_message(os.path.join(self.message_dir, 'newsletter_message4.eml'), 'testuser@donomo.com', 'label4', 'S,F')
        self._process_queue();

        new_conversation = MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, owner = self.user, tags__label = 'label4')[0]
        
        # add a newsletter rule for the sender
        rule = MessageRule(type = MessageRule.NEWSLETTER, owner = self.user, sender_address = new_conversation.messages.all()[0].sender_address)
        rule.save()
        time.sleep(2)
        operations.apply_message_rule(rule)
        time.sleep(2)

        # the new newsletter message goes into the existing aggregate
        # the conversation is still present, with 2 messages
        self.assertEqual(MessageAggregate.objects.filter(status = MessageAggregate.STATUS_READY, 
                                                         owner = self.user, 
                                                         creator__type = MessageRule.NEWSLETTER).count(), 
                                                    1 + original_newsletter_count)

        newsletter = MessageAggregate.objects.get(status = MessageAggregate.STATUS_READY, 
                                                  owner = self.user, 
                                                  creator__type = MessageRule.NEWSLETTER, 
                                                  tags__label = 'label4')
        self.assertEqual(newsletter.messages.all().count(), 3)

        conversation = MessageAggregate.objects.get(status = MessageAggregate.STATUS_READY, owner = self.user, creator__type = MessageRule.CONVERSATION, tags__label = 'label4')
        self.assertEqual(conversation.messages.all().count(), 2)
        
        # Aggregate's name is the subject name of the first message
        self.assertEqual(conversation.name, 'New on The Economist online - 22nd October 2010')
        self.assertEqual(newsletter.name, 'New on The Economist online - 18th October 2010')

# ----------------------------------------------------------------------------

if __name__ == '__main__':
    setup_test_environment()
    unittest.main()
