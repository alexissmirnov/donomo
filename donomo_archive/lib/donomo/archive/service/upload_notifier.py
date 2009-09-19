#!/usr/bin/env python

"""
Once a time treshold is hit without getting any new updates for a user, an
email is sent notifying about the availability of the new batch of uploads.

"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.conf import settings

from donomo.archive import operations, models
from donomo.archive.utils import pdf
from donomo.archive.service import NotReadyException
from cStringIO import StringIO
import datetime
import time
import logging

UPLOAD_NOTIFICATION_TIME_TRESHOLD = 300 # 5 minutes

DEFAULT_INPUTS  = (
    models.AssetClass.DOCUMENT,
    )

DEFAULT_OUTPUTS = ()

DEFAULT_ACCEPTED_MIME_TYPES = (
    models.MimeType.PDF,
    )


##############################################################################

def handle_work_item(processor, item):
    """ Process a work item.  The work item will be provided and its local
        temp directory will be cleaned up by the process driver
        framework.  If this method does not raise an exception the
        work item will also be removed from the work queue.
    """
    document = item['Asset-Instance'].related_document

    logging.debug(document)
    
    # use is_active flag to determine the trial account
    # don't send a link to a document to an inactive account.
    # a trial account cannot download documents
    # since the account is not active.
    # drop the work item
    if not document.owner.is_active:
        return
    
    # Use the timestamp of the complete PDF to determine the creation 
    # date of the document.
    pdf_asset = document.assets.get(
                asset_class__name = models.AssetClass.DOCUMENT,
                mime_type__name   = models.MimeType.PDF)

    # Get all documents tagged by the same upload aggregate tag
    upload_aggregate_tag = document.tags.get(
                                    tag_class = models.Tag.UPLOAD_AGGREGATE)
    
    docs = dict()
    
    #TODO consider denormalizing DB
    # A document may have its own date_created filed that would be set to
    # match the creation time of the DOCUMENT asset with type PDF
    for doc in upload_aggregate_tag.documents.all():
        docs[doc.assets.get(
                asset_class__name = models.AssetClass.DOCUMENT,
                mime_type__name   = models.MimeType.PDF).date_created] = doc
    
    # So we have several documents in a single upload
    # If this document isn't the latest in the upload aggregate then
    # it is clear that it won't be the last one. ever.
    # so we don't need to keep this message around because we know
    # that the last document in the upload aggregate will send 
    # notification email.
    latest_doc = sorted(docs.items(), lambda x, y: cmp(x[1], y[1]))[0]
    
    if len(docs) > 1 and latest_doc[1] != document:
        logging.debug("%d docs tagged with %s. The document %s "\
                      "isn't the last one. %s is. Complete %s by "\
                      "dropping it" 
                      % (len(docs),
                         upload_aggregate_tag,
                         document,
                         latest_doc[1],
                         item))
        return # complete this work item by dropping it
    
    # If, on the other hand, the document is indeed the latest
    # AND a long time have passed since its creation
    # then we need to send notification about this upload
    now = datetime.datetime.fromtimestamp(time.time())
    treshold = datetime.timedelta(0, UPLOAD_NOTIFICATION_TIME_TRESHOLD)
    
    if latest_doc[1] == document and now - latest_doc[0] > treshold:
        send_notification(document.owner, upload_aggregate_tag)
        return

    # In all other cases we keep this work item in the queue
    # by raising NotReady exception
    raise NotReadyException( 
            "Not Ready. Latest %s in upload aggregate tag %s was created "\
            "%s ago, but needs to be older than %s to warrant sending notification yet." % 
                    (document, 
                     upload_aggregate_tag, 
                     now - latest_doc[0],
                     treshold ))
##############################################################################

def send_notification(owner, upload_arrregate):
        logging.info('Email %s about %s' % (owner, upload_arrregate))
        
        current_site = Site.objects.get_current()
        document_count = upload_arrregate.documents.count()
        
        subject = render_to_string('core/upload_notification_email_subject.txt',
                                   { 'site': current_site,
                                    'document_count' : document_count })
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        message = render_to_string('core/upload_notification_email.txt',
                                   { 'user': owner.email,
                                     'tag': upload_arrregate.label,
                                     'document_count' : document_count,
                                     'site': current_site.domain })
        
        send_mail(subject, message, settings.UPLOAD_NOTIFICATION_EMAIL, [owner.email])
                