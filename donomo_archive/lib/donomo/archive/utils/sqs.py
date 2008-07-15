""" Handy API for dealing with SQS
"""

from django.conf          import settings
from boto.sqs.connection  import SQSConnection
from boto.sqs.message     import MHMessage as SQSMessage
from time                 import time, sleep
from logging              import getLogger

#
# pylint: disable-msg=C0103
#
#   C0103 - variables at module scope must be all caps
#

logging = getLogger('SQS')

# -----------------------------------------------------------------------------

def get_connection():
    """ Create a new SQS connection.
    """

    return SQSConnection(
        aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        host                  = settings.SQS_HOST,
        is_secure             = settings.SQS_IS_SECURE )


# -----------------------------------------------------------------------------

def get_queue(
    queue_name,
    sqs_connection = None,
    create = False ):

    """ Get an SQS queue object using the given connection, creating a new
        one if None
    """

    connection = sqs_connection or get_connection()

    if create:
        queue = connection.create_queue(queue_name)
    else:
        queue = connection.get_queue(queue_name)

    if queue is not None:
        queue.set_message_class(SQSMessage)

    return queue

# -----------------------------------------------------------------------------

def create_queue(
    queue_name,
    sqs_connection = None ):

    """ Create (or simply retrieve if it already exists) an SQS queue from the
        given connection, creating a new connection if none is given.
    """

    return get_queue(queue_name, sqs_connection, True)

# -----------------------------------------------------------------------------

def create_message(
    sqs_queue,
    contents = None ):

    """
    Create a new message, optionally seeded from a dictionary
    """

    message = sqs_queue.new_message()

    if contents is not None:
        if isinstance( contents, dict ):
            message.update(contents)
        else:
            message.set_body(contents)

    return message

# -----------------------------------------------------------------------------

def post_message(sqs_queue, message):
    """
    Post a message (textual representation) to SQS
    """
    logging.debug('posting %s to %s' % (message, sqs_queue.id))
    if not isinstance( message, SQSMessage ):
        message = create_message(sqs_queue, message)

    sqs_queue.write(message)

# -----------------------------------------------------------------------------

def get_message(
    sqs_queue,
    visibility_timeout = None,
    max_wait_time      = None,
    interrupt_func     = None,
    poll_frequency     = None ):

    """
    Read a message from SQS.  This call:

       - is non-blocking call if max_wait_time = 0
       - will wait indefinitely if max_wait_time is None
       - will periodically call the supplied interrupt function and return
         if itg returns True
    """

    is_interrupted = interrupt_func or (lambda : False)
    sleep_duration = poll_frequency or 5

    start_time = time()
    while not is_interrupted():
        logging.info('Retrieving message from %s' % sqs_queue.id)
        message = sqs_queue.get_messages(1, visibility_timeout)

        if message and message[0]:
            logging.debug('Returning message=%s'  % message[0])
            return message[0]

        logging.info('No messages found in %s' % sqs_queue.id)
        if max_wait_time == 0:
            return None

        if max_wait_time and max_wait_time < time() - start_time:
            return None

        sleep(sleep_duration)

# -----------------------------------------------------------------------------

def delete_message( message ):
    """
    Delete a message from SQS
    """

    return message.queue.delete_message(message)

# -----------------------------------------------------------------------------
