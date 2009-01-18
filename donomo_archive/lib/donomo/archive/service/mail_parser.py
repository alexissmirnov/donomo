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
from logging                  import getLogger

import email
import re
import os

MODULE_NAME     = os.path.splitext(os.path.basename(__file__))[0]
logging         = getLogger(MODULE_NAME)
DEFAULT_INPUTS  = [ AssetClass.UPLOAD ]
DEFAULT_OUTPUTS = [ AssetClass.UPLOAD ]
DEFAULT_ACCEPTED_MIME_TYPES = [ MimeType.MAIL ]

##############################################################################

def handle_work_item( processor, work_item ):

    """ Pick up an uploaded email and break out each attachment we understand
        into its own upload work item.

    """

    parent_asset = work_item['Asset-Instance']
    upload_class = manager(AssetClass).get( name = AssetClass.UPLOAD )
    counter      = 0

    for part in email.message_from_file(work_item['Local-Path']).walk():
        counter += 1

        mime_type = manager(MimeType).filter(name = part.get_content_type())
        if len(mime_type) == 0:
            continue

        mime_type = mime_type[0]

        if not upload_class.has_consumers(mime_type):
            continue

        file_name = part.get_filename or 'part-%04d.%s' % (
            counter,
            mime_type.extension )

        logging.debug(
            'MessagePart<filename=%s, mime_type=%s>' %(
                file_name,
                mime_type ))

        operations.publish_work_item(
            operations.create_asset_from_stream(
                data_stream  = StringIO(part.get_payload(decode=True)),
                owner        = parent_asset.owner,
                producer     = processor,
                asset_class  = upload_class,
                file_name    = file_name,
                parent_asset = parent_asset,
                child_number = counter,
                mime_type    = mime_type ))

##############################################################################

fax_gateway_regex = re.compile(
    r'\s*Caller-ID: (\d{3})\D*(\d{3})\D*(\d{4})\s*$',
    re.IGNORECASE )

def _get_owner( email_file ):
    """ Check the subject for the fax gateway's regex and check the email
        address of the sender to see if we can decude a user.

    """

    message = email.message_from_file(email_file)

    match = fax_gateway_regex.search(message['subject'])
    if match:
        fax_number = '-'.join(match.groups())
        logging.debug('Found FAX number %s' % fax_number)

        try:
            return manager(FaxNumber).get(
                number = fax_number,
                type   = FaxNumber.USER_SENDS_FROM ).user
        except ObjectDoesNotExist:
            logging.info('No matching user found for %s' % fax_number)

    return User.objects.get(
        email = email.utils.parseaddr(message['from']) [1] )

##############################################################################

@transaction.commit_on_success
def process_mail(processor, local_path):
    """ Process an email message, which is assumed to have been stored on
        the local file system at the path given by local_path.
    """

    operations.publish_work_item(
        operations.create_asset_from_file(
            file_name    = local_path,
            owner        = _get_owner(local_path),
            producer     = processor,
            asset_class  = AssetClass.UPLOAD,
            parent_asset = None,
            child_number = 0,
            mime_type    = MimeType.MAIL ))

##############################################################################

def main():
    """ Program to import mail messages from files on disk """
    import optparse
    parser = optparse.OptionParser()

    parser.add_option(
        '-d',
        '--delete',
        action  ='store_true',
        default = 'False',
        help    = 'Delete each input file after successfully queing it' )

    options, file_name_list = parser.parse_args()

    processor = operations.initialize_processor(
        MODULE_NAME,
        DEFAULT_INPUTS,
        DEFAULT_OUTPUTS,
        DEFAULT_ACCEPTED_MIME_TYPES ) [0]

    # pylint: disable-msg=W0702
    #   -> no exception type given
    for file_name in file_name_list:
        try:
            process_mail(processor, file_name)
        except:
            logging.exception("Failed to process %s" % file_name )
        else:
            if options.delete:
                os.remove(file_name)
    # pylint: enable-msg=W0702

##############################################################################

if __name__ == '__main__':
    main()
