#!/usr/bin/env python

from django.conf import settings
from boto.ec2 import EC2Connection

import optparse

parser = optparse.OptionParser()

parser.add_option('-n', '--num-instances', type='int', default=1)
parser.add_option('-i', '--image')

options, extras = parser.parse_args()

if not options.image:
    parser.error('--image is required')

if len(extras) != 0:
    parser.error('Unrecognized options: %s' % ' '.join(extras))

parameters = [
    'AWS_ACCESS_KEY_ID',
    'AWS_PREFIX',
    'AWS_SECRET_ACCESS_KEY',
    'DATABASE_HOST',
    'DATABASE_PASSWORD',
    'DATABASE_PORT',
    'DATABASE_USER',
    'DEPLOYMENT_MODE',
    'S3_HOST',
    'S3_IS_SECURE',
    'SOLR_HOST',
    'SOLR_IS_SECURE',
    'SOLR_PORT',
    'SQS_HOST',
    'SQS_IS_SECURE',
    'SQS_VISIBILITY_TIMEOUT',
    ]

user_data = '&'.join(['%s=%s' % (p, getattr(settings, p)) for p in parameters ])

conn   = EC2Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
images = conn.get_all_images(options.image)

if len(images) != 1:
    parser.error('Image %s not valid' % options.image_id)

reservation = images[0].run(
    min_count = options.num_instances,
    max_count = options.num_instances,
    user_data = user_data )

for i in reservation.instances:
    print repr(i), i.state
