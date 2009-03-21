"""
Multi-page TIFF parser

"""

from donomo.archive       import models, operations
from donomo.archive.utils import image
from django.conf          import settings

import glob
import os

DEFAULT_INPUTS  = (
    models.AssetClass.UPLOAD,
    )

DEFAULT_OUTPUTS = (
    models.AssetClass.DOCUMENT,
    models.AssetClass.PAGE_ORIGINAL,
    models.AssetClass.PAGE_IMAGE,
    models.AssetClass.PAGE_THUMBNAIL,
    )

DEFAULT_ACCEPTED_MIME_TYPES = (
    models.MimeType.TIFF,
    )

##############################################################################

def handle_work_item(processor, item):

    """ Pick up a (possibly) multipage TIFF upload and turn it into a
        document having (possibly) multiple individual pages.

    """

    new_work    = []
    asset       = item['Asset-Instance']
    local_path  = item['Local-Path']
    work_dir    = os.path.dirname(local_path)
    page_prefix = os.path.join(work_dir, 'page-')

    os.system( 'tiffsplit %r %r' % (local_path, page_prefix) )

    document = operations.create_document(
        owner = asset.owner,
        title = 'Uploaded on %s (%s)' % (
            asset.date_created,
            asset.producer.process ))

    position = 1
    all_page_files = glob.glob('%s*.tif*' % page_prefix)
    all_page_files.sort()
    for page_tiff_path in all_page_files:
        new_work.extend(
            handle_page(
                processor,
                asset,
                document,
                page_tiff_path,
                position ))
        position += 1

    if document is not None:
        new_work.append(
            document.assets.get(
                asset_class__name = AssetClass.DOCUMENT,
                mime_type__name   = MimeType.BINARY ))

    return new_work

##############################################################################

def handle_page(
    processor,
    parent_asset,
    document,
    tiff_original_path,
    position ):


    """ Convert the given TIFF file (representing a s single page) whose path
        is given to a JPEG (via RGBA).  Also create two thumbnails.

    """

    # Stuff we'll need later
    new_page     = operations.create_page(document, position)
    base_name    = os.path.splitext(tiff_original_path)[0]
    rgba_path    = '%s.rgba' % base_name
    jpeg_path    = '%s.jpeg' % base_name
    thumb_path   = '%s-thumbnail.jpeg' % base_name

    # Convert original TIFF to RGBA
    # TODO use convert instead of tiff2rgba
    os.system('tiff2rgba %r %r' % (tiff_original_path, rgba_path))

    # Save the original as JPEG
    image.save(
        image.load(rgba_path),
        jpeg_path)

    # Save the thumbnail as JPEG
    image.save(
        image.thumbnail(
            image.load(rgba_path),
            settings.THUMBNAIL_SIZE),
        thumb_path)

    # Put the assets into the work queue
    return [

        # The oginal full-res page as a TIFF
        operations.create_asset_from_file(
            owner        = document.owner,
            producer     = processor,
            asset_class  = models.AssetClass.PAGE_ORIGINAL,
            file_name    = tiff_original_path,
            related_page = new_page,
            parent       = parent_asset,
            child_number = page.position,
            mime_type    = models.MimeType.TIFF ),

        # The full-res page as a JPEG
        operations.create_asset_from_file(
            owner        = document.owner,
            producer     = processor,
            asset_class  = models.AssetClass.PAGE_IMAGE,
            file_name    = jpeg_path,
            related_page = new_page,
            parent       = parent_asset,
            child_number = page.position,
            mime_type    = models.MimeType.JPEG ),

        # The thumbnail as a JPEG
        operations.create_asset_from_file(
            owner        = document.owner,
            producer     = processor,
            asset_class  = models.AssetClass.PAGE_THUMBNAIL,
            file_name    = thumb_path,
            related_page = new_page,
            parent       = parent_asset,
            child_number = page.position,
            mime_type    = models.MimeType.JPEG ),
        ]

##############################################################################

def redo_page(
    processor,
    parent_asset,
    tiff_original_path,
    position ):

    """ Re-convert the given TIFF file (representing a s single page) to a
        JPEG and a thumbnail.
    """
    try:
        original = parent_asset.children.get(
            child_number = position,
            asset_class = models.AssetClass.PAGE_ORIGINAL)

        image = parent_asset.get(
            child_number = position,
            asset_class = models.AssetClass.PAGE_IMAGE)

        thumbnail = parent_asset.get(
            child_number = position,
            asset_class = models.AssetClass.PAGE_THUMBNAIL)

    except Asset.DoesNotExist:
        logging.debug("Skipping deleted page")
        return

    # Stuff we'll need later
    base_name    = os.path.splitext(tiff_original_path)[0]
    rgba_path    = '%s.rgba' % base_name
    jpeg_path    = '%s.jpeg' % base_name
    thumb_path   = '%s-thumbnail.jpeg' % base_name

    # Convert original TIFF to RGBA
    # TODO use convert instead of tiff2rgba
    os.system('tiff2rgba %r %r' % (tiff_original_path, rgba_path))

    # Save the original as JPEG
    image.save(
        image.load(rgba_path),
        jpeg_path)

    # Save the thumbnail as JPEG
    image.save(
        image.thumbnail(
            image.load(rgba_path),
            settings.THUMBNAIL_SIZE),
        thumb_path)

    # Upload the new asset files
    operations.upload_asset_file( original,  pdf_orig_path )
    operations.upload_asset_file( image,     jpeg_path     )
    operations.upload_asset_file( thumbnail, thumb_path    )

    # Put the assets into the work queue
    return [ original, image, thumbnail ]

##############################################################################
