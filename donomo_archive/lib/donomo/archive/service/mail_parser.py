"""
E-Mail Gateway
"""

#
# pylint: disable-msg=C0103,W0401,W0614
#
#   C0103 - variables at module scope must be all caps
#   W0401 - wildcard import
#   W0614 - unused import from wildcard
#

from cStringIO                import StringIO
from django.db                import transaction
from django.db.models         import ObjectDoesNotExist
from donomo.archive           import operations
from donomo.archive.models    import *
from donomo.archive.utils.misc import extract_text_from_html
from logging                  import getLogger

import datetime
import email
import email.utils
import email.header
import os
import re
import time

MODULE_NAME     = os.path.splitext(os.path.basename(__file__))[0]
logging         = getLogger(MODULE_NAME)
DEFAULT_INPUTS  = [ AssetClass.UPLOAD ]
DEFAULT_OUTPUTS = [ AssetClass.MESSAGE_PART ]
DEFAULT_ACCEPTED_MIME_TYPES = [ MimeType.MAIL ]

#TODO: replace this by django's version
def is_email(s):
    re_email = re.compile(r"(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)",re.IGNORECASE)
    return len(re_email.findall(s)) > 0

def get_or_create_adddress_and_contact(name, address_string, owner):
    if not address_string:
        return None, None
    
    name = header_to_unicode(name) or ''
    
    address = None
    contact = None
    try:
        address = Address.objects.get(email = address_string,
                                      owner = owner)
        # found the email we already have
        # then try to fix the contact's name 
        # do it only if needed i.e. when the name looks like an email address
        # and only when we have a better name to supply i.e. name isn't empty
        contact = address.contact
        
        logging.info('found address %s with the contact %s', address, contact.pk);
        if name and name != '' and is_email(contact.name):
            contact.name = name
            contact.save()
    except Address.DoesNotExist, e:
        address = Address(email = address_string, owner = owner)
        
        # did this email came without a name, then set the name to email
        if name == '':
            name = address_string
        
        # look up the existing contact or create a new one
        # TODO: handle the case of two people having the same name
        contact, created = Contact.objects.get_or_create(name = name, 
                                                        owner = owner)
        address.contact = contact
        address.save()
        logging.info('created address %s with the contact %s (created? %d)', address, contact, created);

            
    return address, contact

# Assume the tags are included in the filename
def get_or_create_tag_from_asset(mail_asset):
    file_name = mail_asset.orig_file_name
    # FIXME
    # I SOOO suck at regex
    # trying to extract the name of the label from 
    # comma-searated list of key/value pairs
    # ...LABEL=label name,FLAGS=....
    label = file_name[file_name.find('LABEL=') + len('LABEL='):]
    label = label[:label.find(',')]
    if label.find('[Gmail]') == 0:
        tag_class = Tag.MAIL_GMAIL_LABEL
    elif label == 'INBOX':
        tag_class = Tag.MAIL_INBOX
    else:
        tag_class = Tag.MAIL_IMAP_FOLDER
    tag, created = Tag.objects.get_or_create(owner = mail_asset.owner,
                                             label = label, 
                                             tag_class = tag_class)
    return tag

def get_mailbox_address_from_asset(mail_asset):
    file_name = mail_asset.orig_file_name

    # FIXME: use regex
    account = file_name[file_name.find('ACCOUNT=') + len('ACCOUNT='):]
    email = account.split(',')[0]
    return get_or_create_adddress_and_contact(mail_asset.owner.username,
                                              email, 
                                              mail_asset.owner)[0]

#TODO
def get_message_tags_from_asset(mail_asset):
    file_name = mail_asset.orig_file_name
    # FIXME
    # I SOOO suck at regex
    # trying to extract the name of the label from 
    # comma-searated list of key/value pairs
    # ...LABEL=label name,FLAGS=....
    flags = file_name[file_name.find('FLAGS=') + len('FLAGS='):]
    flags = flags.split(',')
    
    return 'S' in flags


def test_generate_conversation_summary(raw_message):
    for part in raw_message.walk():
        if( part.get_content_type() != 'multipart/alternative'):
            print part.get_content_type()
            payload = part.get_payload(decode=True).decode('utf8', 'ignore')
            print generate_conversation_summary( payload, part.get_content_type())

##############################################################################
def generate_conversation_summary( body, type, summary_length = 1000 ):
    if type == MimeType.HTML:
        text = extract_text_from_html( body )
    else:
        text = body
        
    text = text.encode('ascii', 'ignore')
    # FIXME: regex?
    # strip consecutive spaces and newlines while
    # avoiding gluing words together
    
    words = text.split(' ')
    summary = StringIO()
    
    for w in words:
        if len(summary.getvalue()) > summary_length:
            break;
        
        if len(w) and w[0] != '\n':
            summary.write( w.strip('\n') + ' ')
    
    # cut the string at summary_length
    return summary.getvalue()[:summary_length]

##############################################################################

#def classify_conversation(conversation):
#    """
#    Assumes 'INBOX' folder. If a conversation is tagged ONLY as 'INBOX' this
#    means it is not classified.
#    
#    Remove from INBOX if it is already tagged with something else.
#    """
#    
#    try:
#        inbox = conversation.tags.get(label = 'INBOX')
#    except Tag.DoesNotExist, e:
#        # already classified. fine
#        return
#    
#    # So INBOX is one folder. Is this conversation already classified
#    # in some other folders?
#    count = conversation.tags.filter(tag_class = Tag.MAIL_IMAP_FOLDER).count()
#    if count > 1:
#        # Yes it is, remove the inbox tag then
#        conversation.tags.remove(inbox)
#        conversation.save()
#        
    
def header_to_unicode(raw_header):
    """
    Decode a message header value and converts it to unicode string
    """
    if not raw_header:
        return None
    
    header = email.header.decode_header(raw_header)[0]
    if header[1] and header[1].lower() == 'iso-8859-1':
        return header[0].decode('iso-8859-1').encode('utf-8')
    elif header[1] and header[1].lower() == 'utf-8':
        return header[0]
    else:
        return unicode(header[0])

def apply_rules(owner, message, raw_message):
    rules = owner.message_rules
    
    for rule in rules.all():
        operations.apply_message_rule_on_message(rule, message, raw_message)


#TODO generate subject for conversations with no-subject emails
#first few words of the body
def handle_work_item( processor, work_item ):
    """ Pick up an uploaded email and break out each attachment we understand
        into its own upload work item.
    """
    asset_list   = []
    parent_asset = work_item['Asset-Instance']
    upload_class = manager(AssetClass).get( name = AssetClass.UPLOAD )
    message_part_class, created = manager(AssetClass).get_or_create( 
                                        name = AssetClass.MESSAGE_PART )
    counter      = 0
    
    conversation_rule, created = MessageRule.objects.get_or_create(
                                    owner = parent_asset.owner, 
                                    type = MessageRule.CONVERSATION)

    raw_message = email.message_from_file(file(work_item['Local-Path']))
    
    # create the record for the sender
    sender = header_to_unicode(raw_message['From'])
    subject = header_to_unicode(raw_message['Subject'])
    in_reply_to = raw_message['In-Reply-To']
    message_date = raw_message['Date']
    message_id = raw_message['Message-ID']
    references = raw_message['References']
    
    sender_name, sender_address_string = email.utils.parseaddr(sender)
    sender_name = sender_name.strip('\'')
    
    sender_address, sender_contact = get_or_create_adddress_and_contact(
                                        sender_name, 
                                        sender_address_string,
                                        parent_asset.owner)
                
    # create a conversation or get one from previously registered email
#    conversation = None
#    in_reply_to_message = None
#    try:
#        in_reply_to_message = Message.objects.get( owner = parent_asset.owner, message_id = in_reply_to )
#        conversation = in_reply_to_message.conversation
#    except Message.DoesNotExist, e:
#        conversation, created = Conversation.objects.get_or_create(
#                    owner = parent_asset.owner,
#                    subject = (subject or '-'). #FIXME regex!
#                            strip('Re: ').strip('RE: ').strip('re: '),
#                    defaults = {'key_participant': sender_address}) 

    
    # get the mailbox account address from asset filename
    # this isn't the same thing as "To:" address because the mail
    # may be sent as BCC and arrive to one of many mailboxes
    # associated to a single account
    mailbox_address = get_mailbox_address_from_asset(parent_asset)
    
    
    # Date field sometimes could be empty
    if message_date:
        message_date = datetime.datetime.fromtimestamp(time.mktime(
                                        email.utils.parsedate(
                                                message_date)))
    else:
        message_date = datetime.datetime.now()

    in_reply_to_message = None
    if in_reply_to:
        in_reply_to_message, created = Message.objects.get_or_create( 
                owner = parent_asset.owner, 
                message_id = in_reply_to,
                mailbox_address = mailbox_address )
    
    # A message could have been created based on a Reference from another
    # message. In this case it will only have owner, message_id and mailbox_address
    message, created = Message.objects.get_or_create(
                    owner = parent_asset.owner,
                    message_id = message_id,
                    mailbox_address = mailbox_address)
    message.subject = subject or ''
    message.date = message_date
    message.reply_to = in_reply_to_message
    message.sender_address = sender_address
    message.save()
    

    # tag unread messages
    # TODO
#    read_flag = get_message_tags_from_asset(parent_asset)
#    if read_flag:
#        seen_tag, created = Tag.objects.get_or_create(tag_class = Tag.MAIL_IMAP_FLAG_SEEN, defaults={label:'Seen'})
#        message.tags.add(seen_tag)
    
    if raw_message.get_all('to'):              
        for a in email.utils.getaddresses(raw_message.get_all('to')):
            address, contact = get_or_create_adddress_and_contact(
                                                          a[0].strip('\''), 
                                                          a[1],
                                                          parent_asset.owner)
            message.to_addresses.add(address)
    
    if raw_message.get_all('cc'):              
        for a in email.utils.getaddresses(raw_message.get_all('cc')):
            address, contact = get_or_create_adddress_and_contact(
                                                          a[0].strip('\''), 
                                                          a[1],
                                                          parent_asset.owner)
            message.to_addresses.add(address)
    
    message.save()
                      
#    classify_conversation(conversation)
    
    apply_rules(parent_asset.owner, message, raw_message)

    # tag all aggregates of this message
    tag = get_or_create_tag_from_asset(parent_asset)
    if tag:
        for aggregate in message.aggregates.all():
            aggregate.tags.add(tag)
            aggregate.save()


    for part in raw_message.walk():
        logging.info('part.get_content_type()=%s', part.get_content_type())
        counter += 1

        mime_type = manager(MimeType).filter(name = part.get_content_type())
        if len(mime_type) == 0:
            logging.info('%s type is unrecognized. Ignoring this message part.', part.get_content_type())
            continue
        else:
            mime_type = mime_type[0]

        payload = part.get_payload(decode=True)
        if not payload:
            logging.info('No payload of part %s. Ignoring this message part.', part.get_content_type())
            continue
        

        if not upload_class.has_consumers(part.get_content_type()):
            logging.info('%s has no consumers for %s(%s)', upload_class, mime_type.name, part.get_content_type())
            #continue

        file_name = part.get_filename() or 'part-%04d.%s' % (
            counter,
            mime_type.extension )

        # Added decode call to avoid errors like
        # UnicodeDecodeError: 'ascii' codec can't decode 
        # byte 0x91 in position 3474: ordinal not in range(128)
        #TODO: figure out why 
        payload = part.get_payload(decode=True).decode('utf8', 'ignore')

        message.summary = generate_conversation_summary(payload, mime_type)
        message.save()

        asset_list.append(
            operations.create_asset_from_stream(
                data_stream  = StringIO(part.get_payload(decode=True)),
                owner        = parent_asset.owner,
                producer     = processor,
                asset_class  = message_part_class,
                file_name    = file_name,
                parent       = parent_asset,
                child_number = counter,
                mime_type    = mime_type,
                related_message = message ))
        
        
    return asset_list

##############################################################################

fax_gateway_regex = re.compile(
    r'\s*Caller-ID: (\d{3})\D*(\d{3})\D*(\d{4})\s*$',
    re.IGNORECASE )


def _get_owner( email_file ):
    """ Check the subject for the fax gateway's regex and check the email
        address of the sender to see if we can decude a user.

    """

    message = email.message_from_file(file(email_file))

    match = fax_gateway_regex.search(message['subject'])
    if match:
        fax_number = '-'.join(match.groups())
        logging.debug('Found FAX number %s', fax_number)

        try:
            return manager(FaxNumber).get(
                number = fax_number,
                type   = FaxNumber.USER_SENDS_FROM ).user
        except ObjectDoesNotExist:
            logging.info('No matching user found for %s', fax_number)

    return User.objects.get(
        email = email.utils.parseaddr(message['to']) [1] )

##############################################################################

@transaction.commit_on_success
def process_mail(owner, processor, local_path):
    """ Process an email message, which is assumed to have been stored on
        the local file system at the path given by local_path.
    """

    return [
        operations.create_asset_from_file(
            file_name    = local_path,
            owner        = owner,
            producer     = processor,
            asset_class  = AssetClass.UPLOAD,
#            parent_asset = None,
            child_number = 0,
            mime_type    = MimeType.MAIL ),
        ]

##############################################################################

def main():
    """ Program to import mail messages from files on disk """
    import optparse
    parser = optparse.OptionParser()

    parser.add_option(
        '-d',
        '--delete',
        action  ='store_true',
        default = False,
        help    = 'Delete each input file after successfully queing it' )
    parser.add_option(
        '-u',
        '--user')

    options, file_name_list = parser.parse_args()
    
    logging.info(options)
    
    owner = User.objects.get(username=options.user)
    
    processor = operations.initialize_processor(
        MODULE_NAME,
        DEFAULT_INPUTS,
        DEFAULT_OUTPUTS,
        DEFAULT_ACCEPTED_MIME_TYPES ) [0]

    # pylint: disable-msg=W0702
    #   -> no exception type given
    for file_name in file_name_list:
        try:
            new_items = process_mail(owner, processor, file_name)
            operations.publish_work_item(*new_items)
        except:
            logging.exception("Failed to process %s", file_name )
        else:
            if options.delete:
                os.remove(file_name)
    # pylint: enable-msg=W0702

##############################################################################

if __name__ == '__main__':
    main()
