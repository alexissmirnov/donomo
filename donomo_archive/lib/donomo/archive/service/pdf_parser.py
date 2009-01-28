"""
Multi-page PDF parser

"""

from donomo.archive       import models, operations
from donomo.archive.utils import pdf, image
from django.conf          import settings

import glob
import os
import logging

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
    is_new      = item['Is-New']
    work_dir    = os.path.dirname(local_path)
    page_prefix = os.path.join(work_dir, 'page-')

    pdf.split_pages( local_path, page_prefix )

    if is_new:
        document = operations.create_document(
            asset.owner,
            title = 'Uploaded on %s (%s)' % (
                asset.date_created,
                asset.producer.process ))
    else:
        document = None, None

    position = 1
    all_page_files = glob.glob('%s*.pdf' % page_prefix)
    all_page_files.sort()
    for page_pdf_path in all_page_files:
        if is_new:
            create_page( processor, asset, document, page_pdf_path,position )
        else:
            redo_page( processor, asset, page_pdf_path, position)
        position += 1

    if document is not None:
        operations.publish_work_item(
            document.assets.get(
                asset_class__name = AssetClass.DOCUMENT,
                mime_type__name   = MimeType.BINARY ))


##############################################################################

def create_page(
    processor,
    parent_asset,
    document,
    pdf_orig_path,
    position ):

    """ Convert the given PDF file (representing a s single page) to a
        JPEG and a thumbnail.
    """

    # Stuff we'll need later
    page         = operations.create_page(document, position)
    base_name    = os.path.splitext(pdf_orig_path)[0]
    jpeg_path    = pdf.convert(pdf_orig_path, 'jpeg')
    thumb_path   = '%s-thumbnail.jpeg' % base_name

    # Save the converted JPEG as a thumbnail JPEG
    image.save(
        image.thumbnail(
            image.load(jpeg_path),
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
            related_page = page,
            parent       = parent_asset,
            child_number = page.position,
            mime_type    = models.MimeType.PDF ),

        # The full-res page as a JPEG
        operations.create_asset_from_file(
            owner        = document.owner,
            producer     = processor,
            asset_class  = models.AssetClass.PAGE_IMAGE,
            file_name    = jpeg_path,
            related_page = page,
            parent       = parent_asset,
            child_number = page.position,
            mime_type    = models.MimeType.JPEG ),

        # The thumbnail as a JPEG
        operations.create_asset_from_file(
            owner        = document.owner,
            producer     = processor,
            asset_class  = models.AssetClass.PAGE_THUMBNAIL,
            file_name    = thumb_path,
            related_page = page,
            parent       = parent_asset,
            child_number = page.position,
            mime_type    = models.MimeType.JPEG ),
        )


##############################################################################

def redo_page(
    processor,
    parent_asset,
    pdf_orig_path,
    position ):

    """ Re-convert the given PDF file (representing a s single page) to a
        JPEG and a thumbnail.
    """
    try:
        asset = {
            'original' : parent_asset.children.get(
                child_number = position,
                asset_class = models.AssetClass.PAGE_ORIGINAL),

            'image' : parent_asset.get(
                child_number = position,
                asset_class = models.AssetClass.PAGE_IMAGE),

            'thumbnail' : parent_asset.get(
                child_number = position,
                asset_class = models.AssetClass.PAGE_THUMBNAIL),
            }

    except models.Asset.DoesNotExist:
        logging.debug("Skipping deleted page")
        return

    # Stuff we'll need later
    base_name    = os.path.splitext(pdf_orig_path)[0]
    jpeg_path    = pdf.convert(pdf_orig_path, 'jpeg')
    thumb_path   = '%s-thumbnail.jpeg' % base_name

    # Save the re-converted JPEG as a new thumbnail JPEG
    image.save(
        image.thumbnail(
            image.load(jpeg_path),
            settings.THUMBNAIL_SIZE),
        thumb_path)

    # Upload the new asset files
    operations.upload_asset_file( asset['original'],  pdf_orig_path )
    operations.upload_asset_file( asset['image'],     jpeg_path     )
    operations.upload_asset_file( asset['thumbnail'], thumb_path    )

    # Put the assets into the work queue
    operations.reprocess_work_item( *asset.values() )

##############################################################################
