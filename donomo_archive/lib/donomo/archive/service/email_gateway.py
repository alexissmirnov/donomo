"""
E-Mail Gateway
"""

from cStringIO                import StringIO
from django.db.models         import ObjectDoesNotExist
from donomo.archive           import operations
from donomo.archive.models    import FaxNumber, User, manager,
from donomo.archive.service   import ProcessDriver
from logging                  import getLogger

import email
import mimetypes
import re

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

logging = getLogger('mail-parser')

# ---------------------------------------------------------------------------

class MailParserDriver(ProcessDriver):

    """
    Adapter for the Mail Parsing Process.

    """

    SERVICE_NAME = 'Mail Gateway'


    DEFAULT_OUTPUTS = [
        ( 'tiff-document', ['docstore.processor.attachment_parser']),
        ]


    ACCEPTED_CONTENT_TYPES = [ 'image/tiff' ]

    def handle_work_item(self, item):
        """
        This is not intended to run as a part of the document
        processing pipeline; rather, it is a gateway process, run on
        demand as mail items arrive.

        """
        raise Exception(
            "%s - The mail parser doesn't run as a driver" % self )

# ---------------------------------------------------------------------------

# Try finding the "Caller-ID: <phone number>" pattern in the subject
# line if found try looking for a user that has this fax # associated
# to the account use that user as the owner of the incoming mail/fax

fax_gateway_regex = re.compile(
    r'\s*Caller-ID: (\d{3})\D*(\d{3})\D*(\d{4})\s*$',
    re.IGNORECASE )

# ---------------------------------------------------------------------------

def extract_owner_from_fax_sender(subject):
    """
    Look for the fax gateway regular expressio in the given subject line

    """
    match = fax_gateway_regex.search(subject)
    if not match:
        logging.debug('FAX number not found in subject')
        return None

    fax_number = '-'.join(match.groups())
    logging.debug('Found FAX number %s' % fax_number)
    try:
        owner = manager(FaxNumber).get(
            number = fax_number,
            type   = FaxNumber.USER_SENDS_FROM ).user
    except ObjectDoesNotExist:
        logging.warn('No matching user found for %s' % fax_number)
        owner = None

    return owner


# ---------------------------------------------------------------------------

def extract_owner_from_mail_sender(sender):
    """
    Lookup the owner based on the sender's email address

    """
    try:
        return User.objects.get( email = email.utils.parseaddr(sender)[1] )
    except ObjectDoesNotExist:
        logging.warn("No matching user found for %s" % sender)
        return None

# ---------------------------------------------------------------------------

def process_mail(local_path):
    """
    Process an email message, which is assumed to have been stored on
    the local file system at the path given by local_path.
    """

    gateway = MailParserDriver()
    message = email.message_from_file(local_path)
    subject = message['subject']
    owner   = None

    logging.debug('processing mail with subject %s' % subject)


    owner = owner or extract_owner_from_fax_sender(subject)
    owner = owner or extract_owner_from_mail_sender(message['from'])

    if not owner:
        logging.error('Unable to determine the owner of this item')
        return False

    counter = 0
    for part in message.walk():
        counter += 1

        content_type = part.get_content_type()
        if not gateway.handles_content_type(content_type):
            continue

        file_name = part.get_filename()
        if not file_name:
            file_name = 'part-%04d%s' % (
                counter,
                mimetypes.guess_extension(content_type) or '.bin')

        logging.debug(
            'part filename=%s, content_type=%s' %(
                file_name,
                content_type ))

        operations.create_upload_from_stream(
            gateway.processor,
            owner,
            file_name,
            StringIO(part.get_payload(decode=True)),
            content_type )

    return True



