"""
Process driver framework for services exposed in the document processing
pipeline.

"""

import donomo.archive.models as core_models
import donomo.archive.utils  as core_utils
from django.contrib.contenttypes.models import ContentType
from django.db.models import get_model
import tempfile
import mimetypes
from socket import gethostbyname, gaierror
from platform import node
import os
import logging as logging_module

logging = logging_module.getLogger('process_driver')

# ---------------------------------------------------------------------------

class ProcessDriver:

    """ Base class for process driver instances
    """

    SERVICE_NAME = None
    DEFAULT_OUTPUTS = None
    ACCEPTED_CONTENT_TYPES = ()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self):

        """ Constructor
        """

        self._processor = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @property
    def processor(self):

        """ The processor represented by this process driver.
        """

        if self._processor is None:
            assert self.SERVICE_NAME, 'ProcessDriver instances require a name'
            self._processor = ProcessDriver.get_or_create_processor(
                self.SERVICE_NAME,
                self.DEFAULT_OUTPUTS or []  )
        return self._processor

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def handles_content_type( self, content_type ):

        """ Returns True if the passed content type is in the list of
            types handled by this service.
        """

        return ( content_type in self.ACCEPTED_CONTENT_TYPES )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __str__(self):

        """ A textual representation of this process driver
        """

        return str(self.processor)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


    def handle_work_item(self, item):

        """ Derived classes must implement this method to handle a work
            item, returning True if the work item has been successfully
            and completely handled.  The return value will be used to
            determine whether or not the work item should be removed
            from the intput queue for this process.

        """

        raise NotImplementedError()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def run_once(self):

        """ Run one iteration of the process loop
        """

        work_item = None
        was_successful = False

        try:
            work_item = self.get_work_item()
        except:
            logging.exception('Failed to retrieve work item')

        if work_item is None:
            return False

        logging.info(
            'Retrieved work item: ' \
                'model = %(Model)s, ' \
                'object = %(Object)s, ' \
                'content-type = %(Content-Type)s' % work_item)

        if not self.handles_content_type( work_item['Content-Type'] ):
            logging.warn(
                'Dropped item of unexpected content type: %(Content-Type)s' \
                    % work_item )
            return True

        try:
            try:
                was_successful = self.handle_work_item(work_item)
            except:
                logging.exception('Failed to handle work item')
        finally:
            self.close_work_item(work_item, was_successful)

        return was_successful

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def create_page_view_from_stream(
        self,
        output_channel,
        page,
        data_stream ):

        """ Create a page view work item on the output channel (given by
            name) from the passed data stream.
        """

        view_type = self.processor.output.get( name = output_channel )

        page_view = core_models.PageView.objects.get_or_create(
            page      = page,
            view_type = view_type ) [0]

        self.create_work_item(
            page_view,
            data_stream )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def create_page_view_from_file(
        self,
        output_channel,
        page,
        path ):

        """ Create a page view work item on the output channel (given by
            name) from the contents of the file denoted by path.
        """
        from __future__ import with_statement
        with open(path, 'rb') as data_stream:
            self.create_work_item_from_stream(
                output_channel,
                page,
                data_stream )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def create_work_item(
        self,
        work_item,
        data_stream ):

        """ Upload a file to S3 then broadcast a message to one or more SQS
            queues.

            work_item:
                Date model object representing a work item - a page view or
                an upload.

            data_stream:
                The actual data that corresponds to this work item. will be
                saved in s3

            content_type:
                Content type of the data comprising work item

        """

        view_type = work_item.view_type
        meta_data = ContentType.objects.get_for_model(work_item)
        s3_path   = work_item.s3_path
        item_type = '%s.%s' % (meta_data.app_label, meta_data.model)

        logging.info(
            'Creating work item: ' \
                'processor = %s, ' \
                'view_type = %s, ' \
                'item_type = %s, ' \
                'item_id = %s' % (
                self.processor,
                view_type,
                item_type,
                work_item.id ))

        core_utils.upload_file_to_s3(
            core_utils.get_s3_bucket(),
            s3_path,
            data_stream,
            view_type.content_type )

        message = {
            'Content-Type' : view_type.content_type,
            'S3-Key'       : s3_path,
            'Model-Name'   : item_type,
            'Primary-Key'  : work_item.id,
            }

        sqs_connection = core_utils.new_sqs_connection()

        for next_processor in view_type.consumers.all():
            logging.info('Notifying %s' % next_processor)
            core_utils.post_message_to_sqs(
                core_utils.create_sqs_queue(
                    next_processor.queue_name,
                    sqs_connection),
                message )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def get_work_item(
        self,
        max_wait_time  = None,
        interrupt_func = None,
        poll_frequency = None ):

        """  Retrieve the next work item for the given processor
        """

        sqs_queue = core_utils.get_sqs_queue(self.processor.queue_name)

        message = core_utils.get_message_from_sqs(
            sqs_queue          = sqs_queue,
            visibility_timeout = self.processor.visibility_timeout,
            max_wait_time      = max_wait_time,
            interrupt_func     = interrupt_func,
            poll_frequency     = poll_frequency )

        if message is None:
            return None

        logging.debug(
            'Retrieved message %s from queue %s' % (
                message,
                self.processor.queue_name ))

        message_content_type = message['Content-Type']

        temp_fd, temp_path = tempfile.mkstemp(
            mimetypes.guess_extension(message_content_type) or '.bin',
            '%s-work-item-' % self.processor.name,
            self.processor.temp_dir )

        logging.debug('Created work item file at %s' % temp_path)
        file_stream = os.fdopen(temp_fd,'wb')

        try:
            try:
                message_s3_path = message['S3-Key']

                metadata = core_utils.download_file_from_s3(
                    core_utils.get_s3_bucket(),
                    message_s3_path,
                    file_stream )
            finally:
                file_stream.close()

            model = get_model(*message['Model-Name'].split('.'))
            instance = model.objects.get(id = int(message['Primary-Key']))

            assert( message_s3_path == instance.s3_path )
            assert( message_content_type == metadata['Content-Type'] )

            message.update( metadata )

            message.update(
                { 'Local-Path'     : temp_path,
                  'Model'          : model,
                  'Object'         : instance,
                  })

            logging.debug(str(message.get_body()))

            return message

        except:
            os.remove(temp_path)
            raise

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def close_work_item(self, message, delete_from_queue):

        """ Finish handling the given work_item, deleting it from the input
            queue if delete_from_queue is true
        """

        logging.info("%s : closing work item %s" % (self, message))

        if delete_from_queue:
            logging.info("Removing %s from message_queue" % message)
            core_utils.delete_message_from_sqs(message)
        local_path = message['Local-Path']
        if os.path.exists(local_path):
            logging.debug('deleting %s' % local_path)
            os.remove(local_path)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def get_or_create_processor(
        name,
        default_outputs ):

        """ Obtain a processor object based on its name and the names of its
            outputs.  The processor will be created if it does not already
            exist.  On creating a processessor, this function assumes it will
            be running on local node.
        """

        process, created = core_models.Process.objects.get_or_create(
            name = name)

        if created:
            logging.info('Registered process: %s' % process)

        if process.outputs.count() == 0:
            logging.info('Adding default output routing for %s' % process)
            for view_name, content_type, consumers in default_outputs:
                view_type = core_models.ViewType.objects.get_or_create(
                    producer = process,
                    name = view_name,
                    content_type = content_type ) [0]
                for consumer in consumers:
                    view_type.consumers.add(
                        core_models.Process.objects.get_or_create(
                            name = consumer ) [0] )
                process.outputs.add(view_type)

        try:
            address = gethostbyname(node())
        except gaierror:
            address = '127.0.0.1'
            logging.exception(
                'Failed to retrieve local address; using %s' % address)

        processor, created = core_models.Processor.objects.get_or_create(
            process = process,
            address = address)

        if created:
            logging.info('Registered processor: %s' % processor)

        logging.debug('Retrieved processor: %s' % processor)

        return processor

