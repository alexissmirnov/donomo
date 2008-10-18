""" Core Models """

#
# pylint: disable-msg=R0903,R0904,W0232
#
#   R0903 - too few public methods
#   R0904 - too many public methods
#   W0232 = class has no __init__ method
#

from django.contrib.auth.models          import User
from django.db                           import models
from django.db.models                    import permalink
from django.utils.timesince              import timesince

###############################################################################

def manager(model):
    """
    Helper function to get the manger for a model, without triggering
    pylint errors.

    """
    return model.objects

###############################################################################

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
        choices     = [ (USER_SENDS_FROM, 'External Sender #'),
                        (USER_RECVS_AT,   'Internal Receive #') ])

    __str__ = lambda self : self.number

    __unicode__ = __str__
    
    class Admin:
        pass


###############################################################################

class MimeType(models.Model):
    """
    A MIME content type for an asset.  This class exists simply to
    normalize the database.
    """

    JPEG = 'image/jpeg'
    PNG  = 'image/png'
    PDF  = 'application/pdf'
    TEXT = 'text/plain'
    HTML = 'text/html'
    MAIL = 'message/rfc822'
    TIFF = 'image/tiff'

    name = models.CharField(
        max_length = 64,
        core       = True,
        blank      = False,
        null       = False,
        unique     = True,
        db_index   = True )

    extension = models.CharField(
        max_length = 15,
        core       = True,
        blank      = True,
        null       = False,
        db_index   = True,
        unique     = True )

    __str__ = lambda self : self.name

    __unicode__ = __str__

    class Admin:
        pass

###############################################################################

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

    mime_types = models.ManyToManyField(
        MimeType,
        related_name = 'consumers' )

    is_gateway = property( lambda self: self.inputs.all().count() == 0 )

    __str__ = lambda self : self.name

    __unicode__ = __str__

    class Admin:
        pass

###############################################################################

class Node(models.Model):
    """ A host participating in the document processing pipeline
    """

    address = models.IPAddressField(
        unique   = True,
        db_index = True )
    __str__ = lambda self : self.address

    __unicode__ = __str__

    class Admin:
        pass

###############################################################################

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

    inputs = property(
        lambda self : self.process.inputs )

    outputs = property(
        lambda self : self.process.outputs )

    __str__ = lambda self : self.name

    __unicode__ = __str__

    class Admin:
        pass

###############################################################################

class TagManager( models.Manager ):

    """ Django model manager class for Tag objects """

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

    def delete_unused_tags( self, owner ):
        """
        Delete all of owner's tags for which there are no tagged documents

        """
        self.filter(
            owner = owner,
            documents__isnull = True).delete()

###############################################################################

class Tag(models.Model):

    """ Documents can be tagged """

    objects = TagManager()

    owner = models.ForeignKey(
        User,
        related_name = 'tags')

    label = models.CharField(
        max_length = 64,
        blank = False,
        null = False,
        db_index = True )

    __str__ = lambda self : self.label

    __unicode__ = __str__

    class Meta:
        """ Constraints """
        unique_together = ( 'owner', 'label' )

    class Admin:
        pass

###############################################################################

class Document(models.Model):

    """ A collection of pages  """

    owner = models.ForeignKey(
        User,
        related_name = 'documents')

    title = models.CharField(
        max_length = 255,
        blank      = True,
        default    = '' )

    num_pages = property(
        lambda self: self.pages.count() )

    tags = models.ManyToManyField(
        Tag,
        related_name = 'documents',
        blank        = True,
        symmetrical  = True )

    __str__ = lambda self : self.title

    __unicode__ = __str__

    get_absolute_url = permalink(
        lambda self : ('document_info', (),  { 'id' : self.pk }))

    class Admin:
        pass
    
###############################################################################

class Page(models.Model):

    """ A positional element of a document """

    owner = models.ForeignKey(
        User,
        related_name = 'pages')

    document = models.ForeignKey(
        Document,
        related_name = 'pages')

    position = models.PositiveIntegerField()

    description = property(
        lambda self: '%s (%s / %s)' %  (
            self.document.title,
            self.position,
            self.document.num_pages ))

    __str__ = lambda self : self.description

    __unicode__ = __str__

    get_absolute_url = permalink(
        lambda self : ('page_info', (), {'id': self.pk }))

    def get_asset(self, asset_class):
        """ Get an asset associated with this page """

        # E1101 = instance of 'Page' has no 'assets' member
        # pylint: disable-msg=E1101

        if isinstance(asset_class, AssetClass):
            return self.assets.get(asset_class__pk = asset_class.pk)
        else:
            return self.assets.get(asset_class__name = asset_class)

        # pylint: enable-msg=E1101
        
    class Admin:
        pass


###############################################################################

class AssetClass(models.Model):
    """
    A semantic tag on an document asset.
    """

    UPLOAD         = 'upload'
    PAGE_ORIGINAL  = 'original'
    PAGE_IMAGE     = 'image'
    PAGE_THUMBNAIL = 'thumbnail'
    PAGE_BANNER    = 'banner'
    PAGE_TEXT      = 'text'

    name = models.CharField(
        max_length = 64,
        unique     = True,
        core       = True,
        db_index   = True,
        help_text  = 'Unique label for this asset class' )

    producers = models.ManyToManyField(
        Process,
        related_name = 'outputs',
        help_text    = 'The processes that create this asset class' )

    consumers = models.ManyToManyField(
        Process,
        related_name = 'inputs',
        help_text    = 'The processes that act on this asset class' )

    __str__ = lambda self : str(self.name)

    __unicode__ = __str__

    def has_consumers(self, mime_type):
        """ True if there is a consumer for assets of the given mime type """
        suffix = isinstance(mime_type, MimeType) and '' or '__name'
        return 0 != self.consumers.filter(
            ** { 'mime_types%s' % suffix : mime_type } ).count()

    class Admin:
        pass

###############################################################################

class AssetManager(models.Manager):

    def create(self, **kwargs):
        kwargs = kwargs.copy()

        asset_class = kwargs.get('asset_class')
        if isinstance( asset_class, str):
            kwargs['asset_class'] = manager(AssetClass).get(name = asset_class)

        mime_type = kwargs.get('mime_type')
        if isinstance( mime_type, str):
            kwargs['mime_type'] = manager(MimeType).get_or_create(
                                                        name = mime_type) [ 0 ]

        if 'file_name' in kwargs:
            kwargs.setdefault('orig_file_name', kwargs.pop('file_name'))

        return models.Manager.create(self, **kwargs)

###############################################################################

class Asset(models.Model):
    """
    A file object stored in the archive.  Assets are tagged with one
    or more asset classes.  Example assets include: uploads,
    thumbnails, ocr text, etc.

    """

    objects = AssetManager()

    owner = models.ForeignKey(
        User,
        related_name = 'assets' )

    producer = models.ForeignKey(
        Processor,
        related_name = 'created_assets')

    asset_class = models.ForeignKey(
        AssetClass,
        related_name = 'assets' )

    parent = models.ForeignKey(
        'Asset',
        null = True,
        default = None,
        related_name = 'children')

    orig_file_name = models.CharField(
        max_length = 255,
        blank      = True )

    mime_type = models.ForeignKey(
        MimeType,
        related_name = 'assets' )

    related_page = models.ForeignKey(
        Page,
        null         = True,
        default      = None,
        related_name = 'assets' )

    date_created = models.DateTimeField(
        auto_now_add = True )

    date_last_modified = models.DateTimeField(
        auto_now = True )

    file_name = property(
        lambda self: 'asset-%d-%s.%s' % (
            self.pk,
            self.asset_class,
            self.mime_type.extension ))

    s3_key = property(
        lambda self: 'user_data/%d/assets/%s' % (
            self.owner.pk,
            self.pk ) )

    description = property(repr)

    consumers = property(
        lambda self:  self.asset_class.consumers.filter(
            mime_types = self.mime_type ))

    __str__ = lambda self : self.file_name

    __unicode__ = __str__

    __repr__ = lambda self : \
        'Asset<'             \
        'asset-id=%s, '      \
        'owner-id=%s, '      \
        'producer=%s, '      \
        'asset_class=%s, '   \
        'content_type=%s>' % (
        self.pk,
        self.owner.pk,
        self.producer,
        self.asset_class,
        self.mime_type )
        
    class Admin:
        pass

###############################################################################

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
###############################################################################
