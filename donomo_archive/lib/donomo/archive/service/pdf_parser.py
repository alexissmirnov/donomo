"""
Multi-page PDF parser

"""

from donomo.archive       import models, operations
from donomo.archive.utils import pdf, image
from django.conf          import settings

import glob
import os

DEFAULT_INPUTS  = (
    models.AssetClass.UPLOAD,
    )

DEFAULT_OUTPUTS = (
    models.AssetClass.PAGE_ORIGINAL,
    models.AssetClass.PAGE_IMAGE,
    models.AssetClass.PAGE_THUMBNAIL,
    )

DEFAULT_ACCEPTED_MIME_TYPES = (
    models.MimeType.PDF,
    )

##############################################################################

def handle_work_item(processor, item):

    """ Pick up a (possibly) multipage PDF upload and turn it into a
        document having (possibly) multiple individual pages.

    """

    asset       = item['Asset-Instance']
    local_path  = item['Local-Path']
    work_dir    = os.path.dirname(local_path)
    page_prefix = os.path.join(work_dir, 'page-')

    pdf.split_pages( local_path, page_prefix )

    document = operations.create_document(
        owner = asset.owner,
        title = 'Uploaded on %s (%s)' % (
            asset.date_created,
            asset.producer.process ))

    position = 1
    for page_pdf_path in glob.glob('%s*.pdf' % page_prefix).sort():
        handle_page(
            processor,
            asset,
            document,
            page_pdf_path,
            position )
        position += 1

##############################################################################

def handle_page(
    processor,
    parent_asset,
    document,
    pdf_orig_path,
    position ):
    """
    Convert the given PDF file (representing a s single page) to a
    JPEG and a thumbnail.
    """

    # Stuff we'll need later
    new_page     = operations.create_page(document, position)
    base_name    = os.path.splitext(pdf_orig_path)[0]
    jpeg_path    = pdf.convert(pdf_orig_path, 'jpeg')
    thumb_path   = '%s-thumbnail.jpeg' % base_name

    # Save the converted JPEG as a thumbnail JPEG
    image.save(
        image.thumbnail(
            image.open(jpeg_path),
            settings.THUMBNAIL_SIZE),
        thumb_path)

    # Put the assets into the work queue
    operations.publish_work_item(

        # The oginal full-res page as a PDF
        operations.create_asset_from_file(
            owner        = document.owner,
            producer     = processor,
            asset_class  = models.AssetClass.PAGE_ORIGINAL,
            file_name    = pdf_orig_path,
            related_page = new_page,
            parent       = parent_asset,
            mime_type    = models.MimeType.PDF ),

        # The full-res page as a JPEG
        operations.create_asset_from_file(
            owner        = document.owner,
            producer     = processor,
            asset_class  = models.AssetClass.PAGE_IMAGE,
            file_name    = jpeg_path,
            related_page = new_page,
            parent       = parent_asset,
            mime_type    = models.MimeType.JPEG ),

        # The thumbnail as a JPEG
        operations.create_asset_from_file(
            owner        = document.owner,
            producer     = processor,
            asset_class  = models.AssetClass.PAGE_THUMBNAIL,
            file_name    = thumb_path,
            related_page = new_page,
            parent       = parent_asset,
            mime_type    = models.MimeType.JPEG ),
        )

##############################################################################
