from boto.s3.connection   import S3Connection
from boto.s3.key          import Key as S3Key
from boto.s3.bucket       import Bucket as S3Bucket

import optparse

def main():
    parser = optparse.OptionParser()
    
    parser.add_option('-k', '--key')
    parser.add_option('-s', '--secret')
    parser.add_option('-b', '--bucket')
    
    options, extras = parser.parse_args()

    print 'will delete %s in %s' % (options.bucket, options.key)
    
    
    conn = S3Connection(
        aws_access_key_id     = options.key,
        aws_secret_access_key = options.secret)
    
    bucket = S3Bucket(conn, options.bucket)

    for key in bucket:
        print 'deleting %s' % key
        bucket.delete_key(key)
        
    print 'deleting bucket'
    bucket.delete()
    
    print 'done.'

if __name__ == '__main__':
    main()
