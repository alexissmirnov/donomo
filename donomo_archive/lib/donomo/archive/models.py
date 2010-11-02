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
from django.contrib.localflavor.us.models import PhoneNumberField
from django.db.models                    import permalink
from django.utils.timesince              import timesince
from datetime import datetime
import time

import logging
logging = logging.getLogger('models')

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

    number = PhoneNumberField(
        blank    = False,
        db_index = True,
        unique   = True )

    type = models.CharField(
        max_length  = 1,
        default     = USER_SENDS_FROM,
        choices     = [ (USER_SENDS_FROM, 'External Sender #'),
                        (USER_RECVS_AT,   'Internal Receive #') ])

    __str__ = lambda self : self.number

    __unicode__ = __str__


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
    BINARY = 'application/octet-stream'
    TEXT = 'text/plain'

    name = models.CharField(
        max_length = 64,
        blank      = False,
        null       = False,
        unique     = True,
        db_index   = True )

    extension = models.CharField(
        max_length = 15,
        blank      = True,
        null       = False,
        db_index   = True,
        unique     = True )

    __str__ = lambda self : self.name

    __unicode__ = __str__


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


###############################################################################

class Node(models.Model):
    """ A host participating in the document processing pipeline
    """

    address = models.IPAddressField(
        unique   = True,
        db_index = True )
    __str__ = lambda self : self.address

    __unicode__ = __str__


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
    USER             = 'user'
    UPLOAD_AGGREGATE = 'upload'
    MAIL_GMAIL_LABEL        = 'mail/gmail-label'
    MAIL_IMAP_FOLDER        = 'mail/imap-folder'
    MAIL_INBOX              = 'mail/imap-inbox'
    MAIL_IMAP_FLAG_SEEN   = 'mail/imap-flag/seen' 

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

    tag_class = models.CharField(
        max_length = 64,
        blank      = True,
        default    = '',
        db_index   = True,
        help_text  = 'Class of this tag' )
    
    date_created = models.DateTimeField(
        auto_now_add = True )

    date_last_modified = models.DateTimeField(
        auto_now = True )


    __str__ = lambda self : self.label

    __unicode__ = __str__

    class Meta:
        """ Constraints """
        unique_together = ( 'owner', 'label' )

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

    class Meta:
        ordering = ('-title',)

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


###############################################################################

class Contact(models.Model):
    BUSINESS = 1
    PERSON = 2
    
    """ A contact has a name and a set of email addresses"""
    owner = models.ForeignKey(
        User,
        related_name = 'contacts')

    name = models.CharField(max_length=128)
    
    type = models.IntegerField(default = PERSON)
    
    tags = models.ManyToManyField(
        Tag,
        related_name = 'contacts',
        blank        = True,
        symmetrical  = True )
    __str__ = lambda self : str(unicode(self).encode('ascii','replace'))
    __unicode__ = lambda self : unicode('%s (%s)' % (self.name, self.pk))

###############################################################################

class Address(models.Model):
    """ Email contact """
    email = models.EmailField(primary_key=True,
                              blank = False)
    contact = models.ForeignKey(Contact,
                                related_name = 'addresses')
    owner = models.ForeignKey(
        User,
        related_name = 'addresses')

    __str__ = lambda self : str(unicode(self).encode('ascii','replace'))
    __unicode__ = lambda self : unicode('%s <%s>' % (self.contact.name, self.email))


    
###############################################################################

class Message(models.Model):
    STATUS_READY = 1 # fully-formed message, all assets are processed
    STATUS_DELETED = -1 # deleted message, assets are no longer accessible
    STATUS_REFERENCE = 0 # message created on the basis of a reference. 
                         # assets are not yet available
    
    def save(self, *args, **kwargs):
        """
        Overwriting save to set created_date and modified_date to utcnow()
        Django uses datetime.now()
        We want to store and transmit only UTC time, and localize it at rendering time
        """
        if not self.created_date:
            self.created_date = datetime.utcnow()
        
        self.modified_date = datetime.utcnow()
        
        super(Message, self).save(*args, **kwargs)
        
    """ A Message  """
    message_id = models.CharField(
        max_length = 512,
        blank = False,
        null = False,
        db_index = True)

    owner = models.ForeignKey(
        User,
        related_name = 'messages')

    subject = models.CharField(
        max_length = 512,
        blank = True,
        null = True)
    
    summary = models.CharField(
        max_length = 1024,
        blank = False,
        null = False)
    
    date = models.DateTimeField(null = True)
    
    modified_date =  models.DateTimeField(null = True)
    
    created_date = models.DateTimeField(null = True)
    
    status = models.IntegerField()

    reply_to = models.ForeignKey('self', 
                                 null = True,
                                 related_name = 'reply_messages')

    sender_address = models.ForeignKey(Address,
                                null = True,
                                related_name = 'sent_messages')
    # Not the same thing as to_address
    # to_address may be empty (in case of BCC or be set to the
    # address of a mailling list
    # mailbox address is the email address of one of the email
    # accounts for a given user
    mailbox_address = models.ForeignKey(Address, 
                                 related_name = 'mailbox_messages')
    
    to_addresses = models.ManyToManyField(Address, 
                                 blank = True,
                                 null = True,
                                 related_name = 'received_messages')

    cc_addresses = models.ManyToManyField(Address, 
                                 blank = True,
                                 null = True,
                                 related_name = 'copied_messages')

    __str__ = lambda self : '%s (%s) on %s' % (self.message_id, self.subject, self.date) 

    __unicode__ = __str__

    def get_asset(self, asset_class, mime_type):
        """ Get an asset associated with this message """

        # E1101 = instance of 'Message' has no 'assets' member
        # pylint: disable-msg=E1101

        logging.info('getting %s %s for Message %s (%s)' %(asset_class, mime_type, self, self.pk))
        if isinstance(asset_class, AssetClass):
            return self.assets.get(asset_class__pk = asset_class.pk, 
                                   mime_type__name = mime_type)
        else:
            all = self.assets.filter(asset_class__name = asset_class, 
                                   mime_type__name = mime_type).all()
            logging.info(all)
            if len(all):
                return all[0] 
            else:
                logging.info('NO ASSET %s %s for Message %s (%s)' %(asset_class, mime_type, self, self.pk))
                return None

###############################################################################
class MessageRule(models.Model):
    """
    """
    CONVERSATION = 1
    NEWSLETTER = 2
    owner = models.ForeignKey(
        User,
        related_name = 'message_rules')
    
    type = models.IntegerField(default = NEWSLETTER)

    sender_address = models.ForeignKey(Address,
                                      null = True,
                                      related_name = 'message_rules')

    __str__ = lambda self : str('%s %s' % (self.owner, (self.type == 
                                        MessageRule.NEWSLETTER and 'N' or 'C')))
    __unicode__ = __str__
    
#    def save(self, *args, **kwargs):
#        logging.info('Saving MessageRule %s', self)
#        super(MessageRule, self).save(*args, **kwargs)
        
###############################################################################

class MessageAggregate(models.Model):
    """ A Message aggregate is a ordered set of messages that match a 
    particular criteria"""
    
    STATUS_READY = 1 # fully-formed aggregate
    STATUS_DELETED = -1 # deleted aggregate

    owner = models.ForeignKey(
        User,
        related_name = 'aggregates')

    creator = models.ForeignKey(
        MessageRule,
        related_name = 'aggregates')
    
    messages = models.ManyToManyField(
            Message,
            related_name = 'aggregates',
            blank = True,
            symmetrical = True )
    
    tags = models.ManyToManyField(
        Tag,
        related_name = 'aggregates',
        blank        = True,
        symmetrical  = True )

    modified_date =  models.DateTimeField(null = True, auto_now = True)
    
    created_date = models.DateTimeField(null = True, auto_now_add = True)
    
    status = models.IntegerField(default = STATUS_READY)

    def _get_latest_message(self):
        messages = self.messages.all().order_by('-date')
        if messages.count():
            return messages[0]
        else:
            return None
    latest_message = property(_get_latest_message)
    
    def _get_latest_sender(self):
        return self.latest_message and self.latest_message.sender_address or None
    latest_sender = property(_get_latest_sender)

    def _get_name_as_initial_subject(self):
        messages = self.messages.all().order_by('date')
        if messages.count():
            return messages[0].subject
        else:
            return ''
    name = property(_get_name_as_initial_subject)
    
    def _get_summary_of_latest_message(self):
        messages = self.messages.all().order_by('date')
        if messages.count():
            return messages[0].summary
        else:
            return ''
    summary = property(_get_summary_of_latest_message)

    __str__ = lambda self : str('%s: %s' % (self.creator__type == 
                                        MessageRule.NEWSLETTER and 'N' or 'C',
                                        self.name))
    __unicode__ = __str__

###############################################################################

class AssetClass(models.Model):
    """
    A semantic tag on an document asset.
    """

    UPLOAD         = 'upload'
    DOCUMENT       = 'document'
    PAGE_ORIGINAL  = 'original'
    PAGE_IMAGE     = 'image'
    PAGE_THUMBNAIL = 'thumbnail'
    PAGE_BANNER    = 'banner'
    PAGE_TEXT      = 'text'
    MESSAGE_PART         = 'message.part'

    name = models.CharField(
        max_length = 64,
        unique     = True,
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
        null = True,
        default = None,
        related_name = 'created_assets')

    asset_class = models.ForeignKey(
        AssetClass,
        related_name = 'assets' )

    parent = models.ForeignKey(
        'Asset',
        null = True,
        default = None,
        related_name = 'children')

    child_number = models.IntegerField()

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

    related_document = models.ForeignKey(
        Document,
        null         = True,
        default      = None,
        related_name = 'assets' )

    related_message = models.ForeignKey(
        Message,
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

    def get_children(self, asset_class):
        return self.children.filter( asset_class__name = asset_class )

    class Meta:
        unique_together = [
            ( 'parent', 'asset_class', 'child_number'),
            ]
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

    __str__ = lambda self : self.name

    __unicode__ = __str__

###############################################################################

class EncryptionKey(models.Model):
    owner = models.ForeignKey(
        User,
        unique = True,
        null   = False,
        related_name = 'encryption_keys' )

    value = models.CharField(
        max_length = 64,
        blank      = False,
        null       = False )
    
    __str__ = lambda self : self.value

    __unicode__ = __str__


###############################################################################
class AccountClass(models.Model):
    EMAIL_GMAIL    = 'email/gmail'
    EMAIL_IMAP     = 'email/imap'

    name = models.CharField(
        max_length = 64,
        blank      = False,
        null       = False )
    
    __str__ = lambda self : self.name

    __unicode__ = __str__

###############################################################################
class Account(models.Model):
    owner = models.ForeignKey(
        User,
        null   = False,
        related_name = 'accounts' )

    id = models.CharField(
        max_length = 64,
        primary_key = True)
    account_class = models.ForeignKey(
        'AccountClass',
        null = True,
        default = None)
    name = models.CharField(
        max_length = 64,
        blank      = False,
        null       = False )
    password = models.CharField(
        max_length = 64,
        blank      = True,
        null       = False )
    server = models.CharField(
        max_length = 64,
        blank      = True,
        null       = False )
    ssl = models.BooleanField(
        blank      = True,
        null       = False )

    __str__ = lambda self : '%s of %s' % (self.name, self.owner.username)

    __unicode__ = __str__
