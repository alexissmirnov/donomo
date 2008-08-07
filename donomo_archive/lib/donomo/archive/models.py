"""
Core Models.
"""

#
# pylint: disable-msg=C0111,E1101,R0903,R0904,W0232,W0612
#
#   C0111 - missing docstring
#   E1101 - instance of Foo has no bar member
#   R0903 - too few public methods
#   R0904 - too many public methods
#   W0232 = class has no __init__ method
#   W0612 - unused variable
#

from __future__                          import with_statement
from cStringIO                           import StringIO
from django.conf                         import settings
from django.contrib.auth.models          import User
from django.contrib.contenttypes         import generic
from django.contrib.contenttypes.models  import ContentType
from django.db                           import models
from django.db.models                    import permalink
from django.utils.timesince              import timesince
from donomo.archive.utils                import s3 as s3_utils
from tempfile                            import gettempdir

import re

# -----------------------------------------------------------------------------

def manager(model):
    """
    Helper function to get the manger for a model, without triggering
    pylint errors.

    """
    return model.objects

# -----------------------------------------------------------------------------

class FaxNumber(models.Model):

    """
    Associates a fax number with a user.  The fax number can be one
    from which the user sends faxes (i.e., an external number from
    which the fax will be sent) or a number at which the user's acount
    receives faxes (i.e., an internal number).
    """

    USER_SENDS_FROM = 'E' # External
    USER_RECVS_AT   = 'I' # Internal

    user = models.ForeignKey(
        User,
        edit_inline = models.TABULAR,
        related_name = 'fax_numbers')

    number = models.PhoneNumberField(
        blank    = False,
        core     = True,
        db_index = True,
        unique   = True )

    type = models.CharField(
        max_length  = 1,
        core        = True,
        default     = USER_SENDS_FROM,
        radio_admin = True,
        choices     = [ (USER_SENDS_FROM, 'External Sender #'),
                        (USER_RECVS_AT,   'Internal Receive #') ])

    class Admin:
        pass

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
        lambda self: self.get_queue_name() )

    visibility_timeout = models.IntegerField(
        default   = 180,
        help_text = 'Time after which the process is deemed to have failed' )

    is_gateway = property( lambda self: self.inputs.all().count() == 0 )

    def __unicode__(self):
        """ The textual representation of this object as a string
        """
        return self.name

    def get_queue_name(self):
        """
        Calculate and cache the queue name for this process.
        """
        if self._queue_name is None:
            self._queue_name = self.illegal_queue_name_chars.sub(
                '_',
                '%s_%s' % (settings.S3_BUCKET, self.name)).strip().lower()
        return self._queue_name

    def inputs_as_text(self):
        """
        Get the list of inputs to this process as a comma seperated list
        """
        return ', '.join( [ str(i) for i in self.inputs.all() ] )

    def outputs_as_text(self):
        """
        Get the list of outputs from this process as a comma seperated list
        """
        return ', '.join( [ str(o) for o in self.outputs.all() ] )

    inputs_as_text.short_description  = 'inputs'
    outputs_as_text.short_description = 'outputs'

    illegal_queue_name_chars = re.compile('[^\w\-]')
    _queue_name = None

    class Admin:
        """ Configuration for admin interface
        """
        list_display = (
            'name',
            'queue_name',
            'inputs_as_text',
            'outputs_as_text',
            )

# -----------------------------------------------------------------------------

class ViewType(models.Model):
    """
    A semantic type of view of a document or page.

    For example:

      - original
      - normalized
      - pdf

    """

    name = models.SlugField(
        max_length = 64,
        unique     = True,
        core       = True,
        db_index   = True,
        help_text  = 'Name or label for this view type' )

    producers = models.ManyToManyField(
        Process,
        related_name = 'outputs',
        help_text    = 'The processes that create this representation' )

    consumers = models.ManyToManyField(
        Process,
        related_name = 'inputs',
        help_text    = 'The processes that act on this representation' )

    def producers_as_text(self):
        """
        Get the set of producers as a comma seperated list
        """
        return ', '.join( [ str(c) for c in self.producers.all() ] )

    def consumers_as_text(self):
        """
        Get the set of consumers as a comma seperated list
        """
        return ', '.join( [ str(c) for c in self.consumers.all() ] )

    def __unicode__(self):
        """
        Human readable description of this view type
        """
        return str(self.name)

    producers_as_text.short_description = 'producers'
    consumers_as_text.short_description = 'consumers'

    class Admin:
        """
        Admin options for ViewType objects

        """
        list_display = (
            'name',
            'producers_as_text',
            'consumers_as_text' )


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

    name = property(
        lambda self: '%s@%s' % (self.process, self.node) )

    queue_name = property(
        lambda self : self.process.queue_name )

    visibility_timeout = property(
        lambda self: self.process.visibility_timeout )

    inputs = property(
        lambda self : self.process.inputs )

    outputs = property(
        lambda self : self.process.outputs )

    temp_dir = property(
        lambda self: gettempdir() )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def __unicode__(self):
        """
        The textual representation of this object as a string

        """
        return self.name

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def inputs_as_text(self):
        """
        The list of inputs formatted as a comma seperated textual list

        """
        return self.process.inputs_as_text

    inputs_as_text.short_description = 'inputs'

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def outputs_as_text(self):
        """
        The list of outputs formatted as a comma seperated textual list

        """
        return self.process.outputs_as_text

    outputs_as_text.short_description = 'outputs'

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

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

    """
    A type of event that can occur over the lifetime of a document.

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

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    class Meta:

        """
        Additional settings for this class of objects

        """

        verbose_name = 'log entry'
        verbose_name_plural = 'log entries'
        ordering = ('-timestamp',)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    class Admin:

        """
        Setting for the administration interface

        """

        list_display = ( 'timestamp', 'event_type', 'processor', 'notes' )

# -----------------------------------------------------------------------------

class TagManager( models.Manager ):

    """
    Django model manager class for Tags
    """

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def get_or_create_from_label_list( self, owner, label_list ):
        """
        Return a list of tags for the given owner, based on the list of
        provided labels.

        """
        return [
            self.get_or_create(
                owner = owner,
                label = label.strip().lower() ) [0]
            for label in label_list ]

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def delete_unused_tags( self, owner ):
        """
        Delete all of owner's tags for which there are no tagged documents

        """
        self.filter(
            owner = owner,
            documents__isnull = True).delete()

# -----------------------------------------------------------------------------

class Tag(models.Model):

    """
    Documents can be tagged
    """

    objects = TagManager()

    owner = models.ForeignKey(
        User,
        related_name = 'tags')

    label = models.CharField(
        max_length = 64,
        blank = False,
        null = False,
        db_index = True )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def __unicode__(self):
        return str(self.label)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

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

    owner = models.ForeignKey(
        User,
        related_name = 'uploads')

    file_name = models.CharField(
        max_length = 255,
        blank      = False )

    view_type = models.ForeignKey(
        ViewType,
        related_name = 'uploads',
        radio_admin  = True,)

    timestamp = models.DateTimeField(
        auto_now_add = True,
        db_index     = True )

    s3_key = property(
        lambda self :  '%s/uploads/%s' % (
            self.owner.username,
            self.pk ) )

    description = property(
        lambda self: '%s %s' % (
            self.view_type.producers.all(),
            self.timestamp ))

    gateway = models.ForeignKey(
        Processor)

    def __unicode__(self):
        """ A textual representation of this upload
        """
        return self.description

    class Admin:
        """ Setting for the administration interface
        """

        list_display = ( 'timestamp', 'owner', 'gateway' )

    class Meta:
        """ Additional settings for this class of objects
        """

        ordering = ('-timestamp', )

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

    num_pages = property(
        lambda self: self.pages.count() )

    history = generic.GenericRelation(EventLog)

    since_created = property(
        lambda self : timesince(self.history[0].timestamp))

    tags = models.ManyToManyField(
        Tag,
        related_name = 'documents',
        blank = True,
        symmetrical = True )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def get_tags_as_text(self):
        """
        The tags associated with this document as a comma seperated list.

        """
        return ', '.join([ str(tag) for tag in self.tags.all() ])

    get_tags_as_text.short_description = 'tags'

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    @permalink
    def get_absolute_url(self):
        """
        Get the URL corresponding to this document.  This uses the permalink
        reverse-lookup mechanism of django.  It returns a triple containing:

          - the view name
          - the list of positional arguments
          - the dictionary of named arguments

        """
        return ( 'document_info',
                 (),
                 { 'id' : self.pk } )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def __unicode__(self):
        """
        Textual label for this document
        """
        return self.title

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    class Admin:
        list_display = (
            'owner',
            'title',
            'num_pages',
            'get_tags_as_text'
            )


# -----------------------------------------------------------------------------

class Page(models.Model):

    """
    Object which represents a page.  There are a number of page views that
    hang off of the page object.

    """

    owner = models.ForeignKey(
        User,
        related_name = 'pages')

    document = models.ForeignKey(
        Document,
        related_name = 'pages')

    position = models.PositiveIntegerField()

    title = property(
        lambda self: self.document.title )

    description = property(
        lambda self: '%s (%s / %s)' %  (
            self.title,
            self.position,
            self.document.num_pages ))

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def get_view(self, view_name):
        """
        Get an object representing a particular view of this page

        """
        return self.page_views.get(view_type__name = view_name)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def get_s3_key(self, view_name):
        """
        Get the path in S3 for a particular view of this page
        """
        return self.get_view(view_name).s3_key

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def download_to_stream( self, view_name, out_stream ):
        """
        Download (to the given output stream) a particular view of this
        page from S3.

        """
        return s3_utils.download_stream(
            s3_utils.get_bucket(),
            self.get_s3_key(view_name),
            out_stream )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def download_to_file( self, view_name, path ):
        """
        Download (to the given output stream) a particular view of this
        page from S3.

        """
        return s3_utils.download_file(
            s3_utils.get_bucket(),
            self.get_s3_key(view_name),
            path )
    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def download_to_memory(self, view_name ):
        """
        Download (to a RAM bufferm) a particular view of this
        page from S3.  The buffer will be in the 'Content' entry
        of the returned meta data dictionary

        """
        stream = StringIO()
        meta_data = self.download_to_stream(view_name, stream)
        meta_data['Content'] = stream.getvalue()
        return meta_data

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def __unicode__(self):
        """
        """
        return self.description

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    @permalink
    def get_absolute_url(self):
        """
        Get the URL corresponding to this page.  This uses the permalink
        reverse-lookup mechanism of django.  It returns a triple containing:

          - the view name
          - the list of positional arguments
          - the dictionary of named arguments

        """
        return ( 'page_info',
                 (),
                 {'id': self.pk })

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    class Admin:
        pass

# -----------------------------------------------------------------------------

class PageView(models.Model):
    """
    A view of a page.  These object primarily track the existence of a
    view and provide some helper properties to map a view into S3.

    A page view is addressed in S3 as

        http(s)://<s3-host>/<bucket>/<owner>/page/<page-id>/<view-type>
    """

    page = models.ForeignKey(
        Page,
        related_name='page_views')

    view_type = models.ForeignKey(
        ViewType,
        related_name = 'page_views',
        radio_admin  = True,)

    history = generic.GenericRelation(EventLog)

    owner = property(
        lambda self: self.page.owner)

    document = property(
        lambda self: self.page.document)

    position = property(
        lambda self: self.page.position)

    s3_key = property(
        lambda self:  '%s/pages/%s/%s' % (
            self.owner.pk,
            self.page.pk,
            self.view_type.name ) )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    @permalink
    def get_absolute_url(self):
        """
        Get the URL corresponding to this document.  This uses the permalink
        reverse-lookup mechanism of django.  It returns a triple containing:

          - the view name
          - the list of positional arguments
          - the dictionary of named arguments

        """
        return ( 'api_page_info',
                 (),
                 { 'id' : self.pk } )

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def __unicode__(self):
        """
        Human readable representation of this page view
        """
        return '[%s] %s' % ( self.view_type, self.page)

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    class Admin:
        """
        Admin options for page view objects

        """
        list_display = (
            'owner',
            'document',
            'position',
            'view_type',
            )

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

