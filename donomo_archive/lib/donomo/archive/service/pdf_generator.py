#!/usr/bin/env python

"""
Wrapper module for the PDF Generation service.  This service gathers
images and ORC text for all pages of a document and assembles them
itno a PDF FILE.

"""

from donomo.archive import operations, models
from donomo.archive.utils import pdf
from donomo.archive.service import NotReadyException


from cStringIO import StringIO
import datetime
import time
import logging
logging    = logging.getLogger('donomo-archive')

UPLOAD_AGGREGATE_TIME_TRESHOLD = 240 # 4 minutes

DEFAULT_INPUTS  = (
    models.AssetClass.DOCUMENT,
    )

DEFAULT_OUTPUTS = (
    models.AssetClass.DOCUMENT,
    )

DEFAULT_ACCEPTED_MIME_TYPES = (
    models.MimeType.BINARY,
    )

##############################################################################

def handle_work_item(processor, item):

    """ Process a work item.  The work item will be provided and its local
        temp directory will be cleaned up by the process driver
        framework.  If this method does not raise an exception the
        work item will also be removed from the work queue.

    """
    document = item['Asset-Instance'].related_document

    num_ocr_pages = document.pages.filter(
        assets__asset_class__name = models.AssetClass.PAGE_TEXT ).count()

    if document.num_pages != num_ocr_pages:
        raise NotReadyException(
            "Postponing PDF generation, OCR not complete for pages")

    # classify the document based on the creation time of its PDF asset
    tag_document(document, datetime.timedelta(0, UPLOAD_AGGREGATE_TIME_TRESHOLD))

    pdf_stream = StringIO(
        pdf.render_document(
            document,
            output_buffer = StringIO(),
            username = document.owner.username,
            title = document.title ).getvalue() )

    pdf_assets = document.assets.filter(
        asset_class__name = models.AssetClass.DOCUMENT,
        mime_type__name   = models.MimeType.PDF )

    if len(pdf_assets) != 0:
        pdf_asset = pdf_assets[0]
        pdf_asset.producer = processor,
        operations.upload_asset_stream(pdf_asset, pdf_stream)
    else:
        pdf_asset = operations.create_asset_from_stream(
                data_stream      = pdf_stream,
                owner            = item['Owner'],
                producer         = processor,
                asset_class      = models.AssetClass.DOCUMENT,
                related_document = document,
                file_name        = document.title,
                parent           = item['Asset-Instance'],
                child_number     = 1,
                mime_type        = models.MimeType.PDF )


    return [ pdf_asset ]


##############################################################################
def tag_document(document, treshold):
    """
    Find the most recently created upload tag.
    Check to see if the current time is close enough for this document to be part
    of this tag. If so, tag it.

    If no close-by tag is found, create one and tag this document with it
    """

    # A document can have only one such tag
    if document.tags.filter(tag_class = models.Tag.UPLOAD_AGGREGATE).count() > 0:
        return
    logging.debug('Classifying %s with treshold %s' %(document, treshold))

    try:
        now = datetime.datetime.fromtimestamp(time.time())

        # get the document with most recently created PDF asset
        most_recent_existing_asset = models.Asset.objects.filter(
                        mime_type__name = models.MimeType.PDF,
                        asset_class__name = models.AssetClass.DOCUMENT).order_by(
                            '-date_created')[0]

        if most_recent_existing_asset.date_created + treshold > now:
            # latest asset is recent, let's use its tag then

            # to get the tag, let's get asset's document
            most_recent_document = most_recent_existing_asset.related_document

            # get the tag object of class "upload aggregate" of this document
            upload_aggregate_tag = most_recent_document.tags.filter(
                                            tag_class = models.Tag.UPLOAD_AGGREGATE)

            if len(upload_aggregate_tag) == 0:
                raise models.Asset.DoesNotExist()
            else:
                upload_aggregate_tag = upload_aggregate_tag[0]
        else:
            # pass the control to exception handling to create a new tag object
            raise models.Asset.DoesNotExist()

    except (IndexError, models.Asset.DoesNotExist):
        logging.debug('Creating new UPLOAD_AGGREGATE tag for time %s' % now)
        # create a tag with current time and tag a given document with it
        upload_aggregate_tag = models.Tag.objects.create(
                                owner = document.owner,
                                label = '%s' % now,
                                tag_class = models.Tag.UPLOAD_AGGREGATE)
        pass

    # tag a given document with this tag
    document.tags.add(upload_aggregate_tag)
    document.save()

##############################################################################
