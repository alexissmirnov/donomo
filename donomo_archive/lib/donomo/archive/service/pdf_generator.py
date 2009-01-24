#!/usr/bin/env python

"""
Wrapper module for the PDF Generation service.  This service gathers
images and ORC text for all pages of a document and assembles them
itno a PDF FILE.

"""

from donomo.archive import operations, models
from donomo.archive.utils import pdf
from cStringIO import StringIO

DEFAULT_INPUTS  = (
    models.AssetClass.DOCUMENT,
    )

DEFAULT_OUTPUTS = (
    models.AssetClass.DOCUMENT,
    )

DEFAULT_ACCEPTED_MIME_TYPES = (
    models.MimeType.BINARY,
    )

class NotReadyException(Exception):
    """ Raised when a document is not ready to have a pdf generated for it """
    pass

##############################################################################

def handle_work_item(processor, item):

    """ Process a work item.  The work item will be provided and its local
        temp directory will be cleaned up by the process driver
        framework.  If this method does not raise an exception the
        work item will also be removed from the work queue.

    """
    document = item['Asset-Instance'].related_document

    num_ocr_pages = models.Asset.objects.filter(
        ower = document.owner,
        asset_class = models.AssetClass.PAGE_TEXT,
        related_page__document = document )

    if document.num_pages != num_ocr_pages:
        raise NotReadyException(
            "Postponing PDF generation, OCR not complete for pages")

    pdf_stream = StringIO(
        pdf.render_document(
            document,
            output_buffer = StringIO(),
            username = document.owner.username,
            title = document.title ).get_value() )

    pdf_assets = document.assets.filter(
        asset_class = models.AssetClass.DOCUMENT,
        mime_type   = models.MimeType.PDF )

    if len(pdf_assets) != 0:
        pdf_asset = pdf_assets[0]
        pdf_asset.producer = processor,
        operations.upload_asset_stream(pdf_asset, pdf_stream)
        operations.publish_work_item(pdf_asset)
    else:
        operations.publish_work_item(
            operations.create_asset_from_stream(
                data_stream      = pdf_stream,
                owner            = item['Owner'],
                producer         = processor,
                asset_class      = models.AssetClass.DOCUMENT,
                related_document = document,
                parent           = item['Asset-Instance'],
                child_number     = 1,
                mime_type        = models.MimeType.PDF ))

##############################################################################
