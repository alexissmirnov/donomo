""" Handy API for dealing with SQS
"""

from django.conf          import settings
from boto.sqs.connection  import SQSConnection
from boto.sqs.message     import MHMessage
from time                 import time, sleep

##############################################################################

def _get_connection():
    """ Create a new SQS connection.

        @rtype: boto.sqs.connection.SQSConnection
        @returns: a new SQS connections configured as per the application
            settings.

    """

    return SQSConnection(
        aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        host                  = settings.SQS_HOST,
        is_secure             = settings.SQS_IS_SECURE )


##############################################################################

def _get_queue():

    """ Get an SQS queue object using the given connection, creating a new
        one if None

        @rtype: boto.sqs.queue.Queue
        @returns: an SQS queue instance for the queue name specified in
            the application settings.
    """

    queue = _get_connection().get_queue( settings.SQS_QUEUE_NAME )
    if queue is not None:
        queue.set_message_class(MHMessage)
    return queue

##############################################################################

def initialize():

    """ Create the SQS queue as per the application settings.

        @returns None

    """

    _get_connection().create_queue(settings.SQS_QUEUE_NAME)

##############################################################################

def post_message_list( msg_list ):

    """ Post a message to SQS

        @type  msg: list of dicts
        @param msg: a list of message dictionaries (name/value pairs)

        @returns: None

    """

    queue = _get_queue()
    for msg in msg_list:
        queue.write(queue.new_message(body = msg))

##############################################################################

def post_message( msg ):

    """ Post a message to SQS

        @type  msg: dict
        @param msg: a dictionary of message fields mapping a string for the
            field name to a string for the field value.

        @returns: None

    """

    post_message_list( [ msg ] )

##############################################################################

def get_message(
    visibility_timeout = None,
    max_wait_time      = None,
    interrupt_func     = None ):

    """ Read the next message from SQS.  This function will retry getting
        the next message using an exponential backoff, up to a max backoff
        time as specified in settings.SQS_MAX_BACKOFF.

        @type  visibility_timeout: positive intger
        @param visibiltiy_timeout: the maximum number of seconds that the
            queue will wait before making the message available to other
            consumers of the queue.  The visiblilty timeout is the maximum
            duration that the message recipient has in which to mark the
            message as handled.

        @type  max_wait_time: non-negative integer or None
        @param max_wait_time: the maximum number of seconds that the
            caller is willing to wait for a message to become available.
            The default is None, meaning the caller is willing to wait
            indefinitely.

        @type  interrupt_func: callable taking no parameters -> bool
        @param inteffupt_func: a function or callable object that takes no
            parameters and returns a boolean.  The interrupt_func will be
            periodically called and the function will be interrupted (and
            will return None) if interrupt_func returns True.

        @rtype: boto.sqs.message.MHMessage or None
        @returns: a message object (dictionary like) or None.

    """

    is_interrupted = interrupt_func or (lambda : False)
    sleep_duration = 1
    sqs_queue      = _get_queue()
    start_time     = time()
    
    if sqs_queue is None:
        return None

    while not is_interrupted():

        message = sqs_queue.read(visibility_timeout)
        if message:
            return message

        max_backoff = settings.SQS_MAX_BACKOFF
        if max_wait_time:
            time_spent = time() - start_time
            if time_spent >= max_wait_time:
                return None
            time_left   = max_wait_time - time_spent
            max_backoff = min( max_backoff, max( time_left, 1))

        for _ in xrange(sleep_duration):
            sleep(1)
            if is_interrupted():
                break

        sleep_duration = int(min( sleep_duration * 2, max_backoff))

##############################################################################

def delete_message( message ):

    """ Delete a message from SQS.

        @param message: a message returned from sqs.get_message

        @returns None

    """

    message.delete()

##############################################################################

def clear_all_messages():
    """ Clear all messages from SQS.  Use with extreme caution.

        @returns None
    """

    import logging

    queue = _get_queue()
    logging.getLogger('sqs').critical('Clearing messages from %s' % queue.url)
    queue.clear()

