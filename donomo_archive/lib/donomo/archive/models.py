"""
Core Models.
"""

from __future__ import with_statement
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models  import ContentType
from django.contrib.contenttypes import generic
from tempfile import gettempdir
from StringIO import StringIO
from django.utils.timesince import timesince
import docstore.core.utils  as core_utils
from docstore.core.utils import make_property
from cStringIO import StringIO

# -----------------------------------------------------------------------------

class Process(models.Model):

    """ A type of process that can be performed on a document.

        For example:

          - import
          - split
          - normalize
          - ocr
          - index
    """

    name = models.SlugField(
        max_length = 64,
        unique     = True,
        db_index   = True,
        help_text  = 'A unique identifier for this process.' )

    queue_name = property(
        lambda self : (
            '%s_%s' % (
                settings.S3_BUCKET,
                self.name )
            ).replace('.','_'))

    visibility_timeout = models.IntegerField(
        default   = 180,
        help_text = 'Time after which the process is deemed to have failed' )

    inputs = models.ManyToManyField(
        'ViewType',
        related_name = 'consumers',
        help_text    = 'process outputs in which this process is interested' )

    def __unicode__(self):
        """ The textual representation of this object as a string
        """
        return self.name

    def inputs_as_text(self):
        return ', '.join(map(str, self.inputs.all()))

    inputs_as_text.short_description = 'inputs'

    def outputs_as_text(self):
        return ', '.join(map(str, self.outputs.all()))

    outputs_as_text.short_description = 'outputs'

    class Admin:
        """ Configuration for admin interface
        """
        list_display = ( 'name', 'queue_name', 'inputs_as_text', 'outputs_as_text' )

# -----------------------------------------------------------------------------

class Node(models.Model):
    """ A host participating in the document processing pipeline
    """

    address = models.IPAddressField(
        unique   = True,
        db_index = True )

    def __unicode__(self):
        """ The textual representation of this object as a string
        """
        return self.address


    class Admin:
        pass

# -----------------------------------------------------------------------------

class Processor(models.Model):

    """ An instance of a process type, given by the ip address on which the
        process is running.
    """

    process = models.ForeignKey(
        Process,
        related_name = 'processors')

    node = models.ForeignKey(
        Node,
        related_name = 'processors')

    @property
    def name(self):
        """ The name of this processor
        """
        return '%s@%s' % (self.process, self.node)

    @property
    def queue_name(self):
        """ The name of the message queue from which this process reads its input
        """
        return self.process.queue_name

    @property
    def visibility_timeout(self):
        """ The duration given to this process to finish handling a message from its
            input queue.  If the process takes longer than this, the message is to
            be reinstated in the input queue.
        """
        return self.process.visibility_timeout

    @property
    def inputs(self):
        """ The set of processes from which this process receives work items.
        """
        return self.process.inputs

    @property
    def outputs(self):
        """ The set of processes to which this process sends work items.
        """
        return self.process.outputs

    temp_dir = gettempdir()

    def __unicode__(self):
        """ The textual representation of this object as a string
        """
        return self.name

    def inputs_as_text(self):
        """ The list of inputs formatted as a comma seperated textual list
        """
        return ', '.join(map(str, self.inputs.all()))

    inputs_as_text.short_description = 'inputs'

    def outputs_as_text(self):
        """ The list of outputs formatted as a comma seperated textual list
        """
        return ', '.join(map(str, self.outputs.all()))

    outputs_as_text.short_description = 'outputs'

    class Admin:
        """ Configuration for admin interface
        """
        list_display = (
            'process',
            'node',
            'queue_name',
            'inputs_as_text',
            'outputs_as_text')

# -----------------------------------------------------------------------------

class EventType(models.Model):

    """ A type of event that can occur over the lifetime of a document.

        For example:

          - Accepted
          - Started
          - Failed
          - Completed
    """

    name = models.SlugField(
        max_length = 32,
        unique     = True,
        db_index   = True)

    def __unicode__(self) :
        return str(self.name)

    class Admin:
        pass

# -----------------------------------------------------------------------------

class EventLog(models.Model):

    _content_type = models.ForeignKey(
        ContentType,
        blank = True,
        null  = True)

    _content_id = models.PositiveIntegerField()

    item = generic.GenericForeignKey()

    processor = models.ForeignKey(
        Processor,
        related_name = 'history')

    timestamp = models.DateTimeField(
        auto_now_add = True)

    event_type = models.ForeignKey(EventType)

    notes = models.TextField(blank=True)

    class Meta:
        """ Additional settings for this class of objects
        """
        verbose_name = 'log entry'
        verbose_name_plural = 'log entries'
        ordering = ('-timestamp',)

    class Admin:
        """ Setting for the administration interface
        """
        list_display = ( 'timestamp', 'event_type', 'processor', 'notes' )

# -----------------------------------------------------------------------------

class Tag(models.Model):

    """
    """

    owner = models.ForeignKey(
        User,
        related_name = 'tags')

    label = models.CharField(
        max_length = 64,
        blank = False,
        null = False,
        db_index = True )

    def __unicode__(self):
        return str(self.label)

    class Meta:
        unique_together = (
            ( 'owner', 'label', ),
            )

# -----------------------------------------------------------------------------

class Upload(models.Model):

    """ A discrete initial data import into the archive.  Each object in the
        archive will ultimately be related to the upload that is responsible
        for its existence.
    """

    class Admin:
        """ Setting for the administration interface
        """

        list_display = ( 'timestamp', 'gateway', 'owner' )

    class Meta:
        """ Additional settings for this class of objects
        """

        ordering = ('-timestamp', )

    owner = models.ForeignKey(
        User,
        related_name = 'uploads')

    gateway = models.ForeignKey(
        Processor,
        related_name = 'uploads')

    timestamp = models.DateTimeField(
        auto_now_add = True,
        db_index     = True )

    @property
    def s3_key(self):
        """ The key (path) used to access this upload in S3
        """
        return '%s/uploads/%s' % ( self.owner.username, self.id )

    @property
    def description(self):
        """ A textual representation of this upload
        """
        return '%s %s' % (self.gateway, self.timestamp)

    def __unicode__(self):
        """ A textual representation of this upload
        """
        return self.description

# -----------------------------------------------------------------------------

class Document(models.Model):

    """ A document.
    """

    owner = models.ForeignKey(
        User,
        related_name = 'documents')

    title = models.CharField(
        max_length = 255,
        blank      = True,
        default    = '' )

    num_pages = property( lambda self: self.pages.count() )

    history = generic.GenericRelation(EventLog)

    since_created = property(lambda self : timesince(self.history[0].timestamp))

    tag_set = models.ManyToManyField(
        Tag,
        related_name = 'documents',
        blank = True,
        symmetrical = True )

    @make_property
    def tags():
        """ Tags for this document
        """
        def fget(self):
            return ', '.join( [ tag.label for tag in self.tag_set.all() ] )
        def fset(self, text):
            phrases = [ part.strip() for part in text.lower().split(',') ]
            self.tag_set = [
                Tag.objects.get_or_create(
                    label = phrase,
                    owner = self.owner) [0]
                for phrase in phrases if len(phrase) > 0 ]
        return locals()

    def get_absolute_url(self):
        """ Public URL of this object
        """
        return Document.get_absolute_url_from_id(self.id)

    @staticmethod
    def get_absolute_url_from_id(id):
        return '/store/doc/%s/' % id

    def __unicode__(self) :
        return self.title

    class Admin:
        list_display = (
            'owner',
            'title',
            'num_pages',
            'tags'
            )


# -----------------------------------------------------------------------------

class Page(models.Model):

    """  Object (actually, just the identifier) which represents a page.
    """

    owner = models.ForeignKey(
        User,
        related_name = 'pages')

    document = models.ForeignKey(
        Document,
        related_name = 'pages')

    binding_date = models.DateTimeField()

    position = models.PositiveIntegerField()

    def get_view(self, view_name):
        return self.page_views.get(view_type__name = view_name)

    def get_s3_path(self, view_name):
        return self.get_views(view_name).s3_path

    def download_to_stream( self, view_name, out_stream ):
        return s3_utils.download_file_from_s3(
            core_utils.get_s3_bucket(),
            self.get_view(view_name).s3_path,
            out_stream )

    def download_to_file( self, view_name, path ):
        with open(path, 'wb') as stream:
            meta_data = self.download_to_stream(view_name, stream)
            meta_data['Local-Path'] = path
            return meta_data

    def download_to_memory(self, view_name ):
        stream = StringIO()
        meta_data = self.download_to_stream(view_name, stream)
        meta_data['Content'] = stream.getvalue()
        return meta_data

    def __unicode__(self):
        return "page" + str(self.id)

    def get_absolute_url(self):
        return '/page/%s/' % self.id

    class Admin:
        pass

# -----------------------------------------------------------------------------

class ViewType(models.Model):
    """ A type of view of a document.

        For example:

          - original
          - normalized
          - pdf
    """

    producer = models.ForeignKey(
        Process,
        related_name = 'outputs',
        help_text    = 'The process that creates this representation' )

    name = models.SlugField(
        max_length = 64,
        #core       = True,
        db_index   = True )

    content_type = models.CharField(
        max_length   = 64,
        blank        = False,
        #core         = True,
        help_text    = 'MIME content type for this representation' )

    def consumers_as_text(self):
        return ', '.join(map(str, self.outputs.all()))

    consumers_as_text.short_description = 'consumers'

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (
            ( 'producer', 'name' ),
            )

    class Admin:
        list_display = ( 'name', 'producer', 'content_type', 'consumers_as_text' )


# -----------------------------------------------------------------------------

class PageView(models.Model):
    """
    A view of a page.  These object primarily track the existence of a
    view and provide some helper properties to map a view into S3.

    A page view is addressed in S3 as

        http(s)://<s3-host>/<bucket>/<owner>/page/<page-id>/<view-type>
    """

    page = models.ForeignKey(Page, related_name='page_views')

    view_type = models.ForeignKey(
        ViewType,
        related_name = 'page_views',
        radio_admin  = True,)

    history = generic.GenericRelation(EventLog)

    @property
    def s3_key(self):
        """
        The key (path) used to access this page view in S3
        """
        return '%s/pages/%s/%s' % (
            self.page.owner.username,
            self.page.id,
            self.view_type.name ))

    def get_absolute_url(self):
        return self.get_s3_url()

    def __unicode__(self):
        return 'Page %s (%s)' % ( self.page, self.view_type)

    class Admin:
        list_display = (
            'page__owner',
            'page__document',
            'page__position',
            'view_type')

# -----------------------------------------------------------------------------

class Query(models.Model):
    """
    A query that the user has previously run
    """

    owner = models.ForeignKey(
        User,
        related_name = 'queries')

    last_run = models.DateTimeField(
        db_index   = True,
        auto_now = True)

    since_last_run = property(lambda self : timesince(self.last_run))

    name = models.CharField(
        max_length = 64,
        blank      = True,
        db_index   = True)

    value = models.CharField(
        max_length = 255,
        db_index   = True)

    class Admin:
        pass
