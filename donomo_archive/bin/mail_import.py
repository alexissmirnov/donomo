#!/usr/bin/env python
"""Unpack a MIME message and post its part to a URL"""

import os
import sys
from optparse import OptionParser

import email
from email.utils import parseaddr
import errno
import mimetypes
from docstore import log

from docstore.core.models import *
from django.contrib.auth.models import User
from docstore.apps.account.models import UserProfile

from docstore.core.api import create_doc_with_initial_view
from docstore.core.api import get_or_create_processor
import tempfile
import StringIO
import shutil
import re

DEFAULT_OUTPUTS = (
    ('email', 'message/rfc822', ['docstore.processor.mail_parser']),
    )

PHONE_NUMBER_EX = "Caller-ID: (\d{3})\D*(\d{3})\D*(\d{4})$"
#"^\(?(?<AreaCode>[2-9]\d{2})(\)?)(-|.|\s)?(?<Prefix>[1-9]\d{2})(-|.|\s)?(?<Suffix>\d{4})$"
# "^\(\d{3}\) ?\d{3}( |-)?\d{4}|^\d{3}( |-)?\d{3}( |-)?\d{4}$"

def main():
    parser = OptionParser(usage="""\
Unpack a MIME message into 3s. MIME message is read from standard input

Usage: %prog < mime-message
""")

    directory = tempfile.mkdtemp()

    phone_number_regex = re.compile(PHONE_NUMBER_EX)
    
    try:
        message_string = StringIO.StringIO(sys.stdin.read())

        msg = email.message_from_file(message_string)

        message_string.seek(0)

        subject = msg['subject']

        log.debug('processing mail with subject %s' % subject)

        # Try finding the "Caller-ID: <phone number>" pattern in the subject line
        # if found try looking for a user that has this fax # associated to the account
        # use that user as the owner of the incoming mail/fax
        m = phone_number_regex.search(subject)
        owner = None
        if m:
            log.debug('Found FAX number %s' % m.group())
            try:
                fax_number = '-'.join(m.groups())
                owner = UserProfile.objects.get(fax_number = fax_number).user
            except UserProfile.NotFound:
                pass
        else:
            log.debug('FAX number not found in subject')
        
        if not owner:
            try:
                log.debug('parseaddr returns %s' % str(parseaddr(msg['from'])))
                owner = User.objects.get(email=parseaddr(msg['from'])[1])
            except Exception, e:
                log.warn("user with email address %s not found. ignoring message" % msg['from'])
                return


        mail_gateway = get_or_create_processor(
            'docstore.gateway.mail',
            DEFAULT_OUTPUTS)

        create_doc_with_initial_view(
            mail_gateway,
            mail_gateway.outputs.get( name = 'email'),
            owner,
            subject,
            message_string)

    finally:
        shutil.rmtree(directory)

if __name__ == '__main__':
    main()
