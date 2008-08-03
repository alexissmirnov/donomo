#!/usr/bin/env python
"""
Imports a file into donomo
"""

from __future__ import with_statement
from optparse                                   import OptionParser
from logging                                    import getLogger
from django.contrib.auth.models                 import User
from django.conf                                import settings
from donomo.archive                             import operations as ops
from donomo.archive.service                     import tiff_parser, pdf_parser
import tempfile
import shutil
import os
import sys

logging    = getLogger('donomo-archive')

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = OptionParser(usage="""\
Imports a file into archive

Usage: %prog -e user's mail address [-t <title>][files]
""")

    parser.add_option('-e', '--email')
    parser.add_option('-t', '--title')

    options, file_names = parser.parse_args(argv[1:])

    if not options.email:
        parser.error('user is a required parameter')
    if len(file_names) == 0 and not options.title:
        parser.error('title is required if not reading from a file')

    try:
        directory = tempfile.mkdtemp()
        owner = User.objects.get(email=options.email)
        for file_name in len(file_names) > 0 and file_names or ['<STDIN>']:
            file_type = os.path.splitext(file_name)[1]
            with (open(file_name, 'rb')) as stream:
                title = options.title or os.path.basename(file_name).rsplit('.',1)[0]

                print "Importing: ", title

                if file_type == '.tiff':
                    upload(tiff_parser, owner, title, stream)
                elif file_type == '.pdf':
                    upload(pdf_parser, owner, title, stream)
    finally:
        shutil.rmtree(directory)

def upload(parser_module, owner, title, stream):
    driver = parser_module.get_driver()
    processor, created = ops.get_or_create_processor(
                parser_module.MODULE_NAME,
                driver.DEFAULT_OUTPUTS)
    ops.create_upload_from_stream(
              processor,
              owner,
              title,
              stream,
              driver.ACCEPTED_CONTENT_TYPES[0])
    if created:
        logging.warn('the processor %s should have been created by now' 
                     % processor )

if __name__ == '__main__':
    print "import_file is importing to %s" % settings.S3_BUCKET
    main()

