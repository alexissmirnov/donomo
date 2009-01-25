"""
Utility script to upload a file into the archive
"""

from donomo.archive import models, operations
from django.db import transaction
import os
import optparse
import logging

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
logging = logging.getLogger(MODULE_NAME)
DEFAULT_INPUTS  = ()
DEFAULT_OUTPUTS = [ models.AssetClass.UPLOAD ]
DEFAULT_ACCEPTED_MIME_TYPES = ()

##############################################################################

@transaction.commit_on_success
def upload_file( processor, user, local_path ):
    """ Transactionally upload a new work item """
    operations.publish_work_item(
        operations.create_asset_from_file(
            file_name    = local_path,
            owner        = user,
            producer     = processor,
            child_number = 0,
            asset_class  = models.AssetClass.UPLOAD ))

##############################################################################

def main():
    """ Program to import mail messages from files on disk """
    parser = optparse.OptionParser()

    parser.add_option(
        '-d',
        '--delete',
        action  ='store_true',
        default = False,
        help    = 'Delete each input file after successfully queing it' )

    parser.add_option(
        '-u',
        '--user',
        help    = 'The username, email, or openid of the owner' )

    options, file_name_list = parser.parse_args()

    if not options.user:
        parser.error('User is required')

    if len(file_name_list) == 0:
        parser.error('No files specified')

    try:
        user = models.User.objects.get( email = options.user )
    except models.User.DoesNotExist:
        user = models.User.objects.get( username = options.user )

    processor = operations.initialize_processor(
        MODULE_NAME,
        DEFAULT_INPUTS,
        DEFAULT_OUTPUTS,
        DEFAULT_ACCEPTED_MIME_TYPES ) [0]

    # pylint: disable-msg=W0702
    #   -> no exception type given
    for file_name in file_name_list:
        try:
            upload_file(processor, user, file_name)
        except:
            logging.exception('Failed to process %s' % file_name )
        else:
            if options.delete:
                os.remove(file_name)
    # pylint: enable-msg=W0702

##############################################################################

if __name__ == '__main__':
    main()
