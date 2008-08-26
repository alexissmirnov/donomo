""" Handy API for dealing with S3
"""

from django.conf          import settings
from boto.s3.connection   import S3Connection
from boto.s3.key          import Key as S3Key
from boto.s3.bucket       import Bucket as S3Bucket


##############################################################################

def _get_connection():
    """ Get a new S3 connection object based on the settings for this
        application.

        @rtype: boto.s3.connection.S3Connection
        @returns: an S3 connection object corresponding to the application
            settings.
    """

    return S3Connection(
        aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        host                  = settings.S3_HOST,
        is_secure             = settings.S3_IS_SECURE)

##############################################################################

def _get_bucket():

    """ Get an S3 bucket object for the bucket name given in the settings
        for this application.

        @rtype: boto.s3.bucket.Bucket
        @returns: An S3 bucket object for the bucket name set in the
            settings for the application.
    """

    return S3Bucket(
        connection = _get_connection(),
        name       = settings.S3_BUCKET_NAME)

##############################################################################

def _get_key( s3_path ):

    """ Helper function to retrieve an S3Key object representing the given
        path in S3.

        @type  s3_path: string
        @param s3_path: the path (not including the bucket name) in S3
            for which to generate the URL.

        @rtype:   boto.s3.key.Key
        @returns: An S3 Key object for the given s3_path.
    """

    return S3Key(
        bucket = _get_bucket(),
        name   = s3_path )

##############################################################################

def initialize():
    """ Create the S3 bucket as per the settings.

        @returns: None

    """

    _get_connection().create_bucket(settings.S3_BUCKET_NAME)

##############################################################################

def generate_url(
    s3_path,
    expires_in,
    method     = 'GET',
    headers    = None,
    query_auth = True ):

    """ Generate an S3 URL, with or without query authentication.  A URL
        with query authentication is useful for temporarily granting
        or delegating access to a specific S3 request.

        @type  s3_path: string
        @param s3_path: the path (not including the bucket name) in S3
            for which to generate the URL.

        @type  expires_in: int
        @param expires_in: How long (in seconds) the generatedurl should
            be valid for.  An expiry time is generated as the given offset
            from the local machine's current UTC.  As such, it is expected
            that the local machine have the correct time (via NTP, for
            example).

        @type  method: string
        @param method: The method to use for retrieving the file
            (default is GET)

        @type  headers: dict
        @param headers: Any additional headers that will be sent with
            the actual request.  For example, if the request is a PUT
            being performed with query-auth and you intend to also set
            the Content-Type, then the content type must be given as a
            header.

        @type  query_auth: bool
        @param query_auth:

        @rtype: string
        @return: The URL to access the key

    """

    return _get_connection().generate_url(
        expires_in = expires_in,
        method     = method,
        bucket     = settings.S3_BUCKET_NAME,
        key        = s3_path,
        headers    = headers,
        query_auth = query_auth )

##############################################################################

def upload_from_stream( s3_target_path, source_data_stream, content_type ):

    """ Upload a file to the given dest path in the given s3 bucket.  The
        file data is read from data stream, which must implement the
        file interface, and the content type will be set.

        @type  s3_target_path: string
        @param s3_target_path: the path (not including the bucket name)
            in S3 to which the data should be written.

        @type  source_data_stream: file or file-like object
        @param source_data_stream: the file object (file, StringIO, etc)
            from which the data to be uploaded will be taken.

        @type  content_type: string
        @param content_typoe: the MIME content type of the data being
            uploaded.  This value will be returned by S3 when the data
            is subsequently downloaded.

        @returns: None

    """

    _get_key( s3_target_path ).set_contents_from_file(
        fp      = source_data_stream,
        headers = { 'Content-Type' : content_type })

##############################################################################

def upload_from_file( s3_target_path, local_source_path, content_type ):

    """ Upload a file to the given target path on S3.  The file's data is
        read from local_source_path

        @type  s3_target_path: string
        @param s3_target_path: the path (not including the bucket name)
            in S3 to which the data should be written.

        @type  local_source_path: string
        @param local_source_path: the path on the local file system from
            which the data to be uploaded will be taken.

        @type  content_type: string
        @param content_typoe: the MIME content type of the data being
            uploaded.  This value will be returned by S3 when the data
            is subsequently downloaded.

        @returns: None
    """

    # TODO - encrypt file first!
    _get_key( s3_target_path ).set_contents_from_filename(
        filename = local_source_path,
        headers  = { 'Content-Type' : content_type } )

##############################################################################

def file_exists( s3_path ):

    """ Check if a path exists in S3

        @type  s3_path: string
        @param s3_path: the path (not including the bucket name) in S3
            for which to check existenced.

        @rtype: bool
        @returns: whether or not the given key exists in S3.

    """

    return _get_key(s3_path).exists()

##############################################################################

def download_to_stream( s3_source_path, output_stream ):

    """ Download a file from S3 to the given path on the local disk.

        @type  s3_source_path: string
        @param s3_source_path: the path (not including the bucket name)
            in S3 from which to download data.

        @type  output_stream: file or file-like object
        @param output_stream: the output stream (for example, a file or
            a StringIO object) to which the contents of the file at
            s3_source_path should be downloaded.

        @rtype: dict
        @returns: a dictionary containing the files meta-data.  The
            supplied fields are Content-Type, Content-Length, ETag,
            and Last_Modified.

    """

    s3_key = _get_key( s3_source_path )

    s3_key.get_contents_to_file( output_stream )

    return {
        'Content-Type'   : s3_key.content_type,
        'Content-Length' : s3_key.size,
        'ETag'           : s3_key.etag,
        'Last-Modified'  : s3_key.last_modified,
        }

##############################################################################

def download_to_file( s3_source_path, local_dest_path ):

    """ Download a file from S3 to the given path on the local disk.

        @type  s3_source_path: string
        @param s3_source_path: the path (not including the bucket name)
            in S3 from which to download data.

        @type  local_dest_path: string
        @param local_dest_path: the path on the local file system to
            which the contents of s3_source_path should be written.
            If the last-modified-date of the file is set in S3, this
            function will attempt to set it on the local copy as well.

        @rtype: dict
        @returns: a dictionary containing the files meta-data.  The
            supplied fields are Content-Type, Content-Length, ETag,
            Last_Modified, and Local_path.
    """

    s3_key = _get_key( s3_source_path )

    s3_key.get_contents_to_filename( local_dest_path )

    # TODO - add decryption
    return {
        'Content-Type'   : s3_key.content_type,
        'Content-Length' : s3_key.size,
        'ETag'           : s3_key.etag,
        'Last-Modified'  : s3_key.last_modified,
        'Local-Path'     : local_dest_path,
        }

##############################################################################

def delete_file( s3_path ):
    """ Delete a file from S3

        @type  s3_path: string
        @param s3_path: The path (not including the bucket name) of the
            s3_key to be deleted.

        @returns: None
    """

    return _get_bucket().delete_key(s3_path)

##############################################################################
