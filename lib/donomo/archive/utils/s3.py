""" Handy API for dealing with AWS
"""

from django.conf          import settings
from boto.s3.connection   import S3Connection, S3ResponseError
from boto.s3.key          import Key as S3Key
from logging              import getLogger

logging = getLogger('S3')

# -----------------------------------------------------------------------------

def get_connection():
    """ Get a new S3 connection object
    """

    return S3Connection(
        aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        host                  = settings.S3_HOST,
        is_secure             = settings.S3_IS_SECURE )

# -----------------------------------------------------------------------------

def get_bucket(
    bucket_name   = settings.S3_BUCKET,
    s3_connection = None,
    create        = False ):

    """ Get an S3 bucket from the given connection, creating a new connection
        if none is given.  Optionally create the bucket if it doesn't exist.
    """

    connection = s3_connection or get_connection()

    if create:
        return connection.create_bucket(bucket_name)

    return connection.get_bucket(bucket_name)

# -----------------------------------------------------------------------------

def _get_object(
    s3_bucket,
    path ):

    """ Retrieve an S3Key object representing a particular path/object in S3.
    """

    return S3Key( s3_bucket, name=path )

# -----------------------------------------------------------------------------

def upload_stream(
    s3_bucket,
    dest_path,
    data_stream,
    content_type = None):

    """ Upload a file to the given dest path in the given s3 bucket. The
        file data is read from data stream, which must implement the file
        interface, and the content type will be set.
    """

    _get_s3_object(s3_bucket, dest_path).set_contents_from_file(
        data_stream,
        { 'Content-Type' : content_type or 'application/octet-stream' })

# -----------------------------------------------------------------------------

def upload_file(
    s3_bucket,
    dest_path,
    source_path,
    content_type = None ):

    """ Upload a file to the given dest path in the given s3 buket.  The
        file data is read from source_path
    """

    with open( source_path, 'rb') as data_stream:
        upload_stream(
            s3_bucket,
            dest_path,
            data_stream
            content_type or mimetypes.guess_type(source_path)[0] )

# -----------------------------------------------------------------------------

def file_exists_in_s3(
    s3_bucket,
    path ):

    """ Check if a path exists in S3
    """

    try:
        return s3_bucket.get_key(path) is not None
    except S3ResponseError, error:
        if error.status == 404:
            return False
        raise

# -----------------------------------------------------------------------------

def download_stream(
    s3_bucket,
    src_path,
    out_stream ):

    """ Download a file from S3 to the given path on the local disk.

        Returns a dictionary containing the files meta-data.
    """

    s3_object = _get_s3_object( s3_bucket, src_path )

    logging.debug('Downloading %s' % s3_object.name)

    s3_object.get_contents_to_file(out_stream)

    return {
        'Content-Type'   : s3_object.content_type,
        'Content-Length' : s3_object.size,
        'ETag'           : s3_object.etag,
        'Last-Modified'  : s3_object.last_modified,
        }

# -----------------------------------------------------------------------------

def download_file(
    s3_bucket,
    src_path,
    dest_path ):

    """ Download a file from S3 to the given path on the local disk.

        Returns a dictionary containing the files meta-data.
    """

    s3_object = _get_s3_object( s3_bucket, src_path )

    logging.debug('Downloading %s' % s3_object.name)

    s3_object.get_contents_to_filename(dest_path)

    return {
        'Content-Type'   : s3_object.content_type,
        'Content-Length' : s3_object.size,
        'ETag'           : s3_object.etag,
        'Last-Modified'  : s3_object.last_modified,
        'Local-Path'     : dest_path,
        }

# -----------------------------------------------------------------------------

def delete_file_from_s3(
    s3_bucket,
    path ):

    """ Delete a file from S3
    """

    return s3_bucket.delete_key(path)

# -----------------------------------------------------------------------------
