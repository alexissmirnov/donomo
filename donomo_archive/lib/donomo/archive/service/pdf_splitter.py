"""
Multi-page PDF parser

"""

from donomo.archive       import models, operations
from donomo.archive.utils import pdf

import glob
import os
import logging

DEFAULT_INPUTS  = (
    models.AssetClass.UPLOAD,
    )

DEFAULT_OUTPUTS = (
    models.AssetClass.PAGE_ORIGINAL,
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
    asset_list  = []

    pdf.split_pages( local_path, page_prefix )

    if asset.get_children(models.AssetClass.PAGE_ORIGINAL).count() == 0:
        document = operations.create_document(
            asset.owner,
            title = 'Uploaded on %s (%s)' % (
                asset.date_created,
                asset.producer.process ))
    else:
        document = None

    position = 1
    all_page_files = glob.glob('%s*.pdf' % page_prefix)
    all_page_files.sort()

    for page_pdf_path in all_page_files:
        if document:
            page_asset = operations.create_asset_from_file(
                owner        = document.owner,
                producer     = processor,
                asset_class  = models.AssetClass.PAGE_ORIGINAL,
                file_name    = page_pdf_path,
                related_page = operations.create_page(document, position),
                parent       = asset,
                child_number = position,
                mime_type    = models.MimeType.PDF ),
        else:
            page_asset = asset.children.get(position=position)
            operations.upload_asset_file(page_asset, page_pdf_path)

        asset_list.append(page_asset)
        position += 1

    asset_list.append(
        document.assets.get(
            asset_class__name = models.AssetClass.DOCUMENT,
            mime_type__name   = models.MimeType.BINARY ))

    return asset_list

##############################################################################
