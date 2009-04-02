
"""
Wrapper module for the OCR service.  This service converts images to
text/html representations, suitable for indexing in a search engine.

"""

from donomo.archive import operations, models
import donomo.billing.models

import os
import logging

DEFAULT_INPUTS  = (
    models.AssetClass.PAGE_IMAGE,
    )

DEFAULT_OUTPUTS = (
    models.AssetClass.PAGE_TEXT,
    )

DEFAULT_ACCEPTED_MIME_TYPES = (
    models.MimeType.JPEG,
    models.MimeType.PNG,
    models.MimeType.TIFF,
    )

class OCRFailed(Exception):
    pass

##############################################################################

def image_to_html( in_path, out_path = None ):

    """ Uses an OCR engine (ocropus) to convert JPEG source file into an
        HTML output file.

    """

    if out_path is None:
        out_path = '%s.html' % in_path

    #if 0 != os.system('cat /tmp/ocrstub.html > %r' % out_path):
    if 0 != os.system('/usr/local/bin/ocroscript recognize %r > %r' % (in_path, out_path)):
        raise OCRFailed( 'Failed to OCR: %r' % in_path)

    return out_path

##############################################################################

def handle_work_item(processor, item):

    """ Process a work item.  The work item will be provided and its local
        temp directory will be cleaned up by the process driver framework.
        If this method does not raise an exception the work item will
        also be removed from the work queue.

    """
    try:
        new_work = []
        parent_asset = item['Asset-Instance']
        new_work.append(
            operations.create_asset_from_file(
                owner        = item['Owner'],
                producer     = processor,
                asset_class  = models.AssetClass.PAGE_TEXT,
                file_name    = image_to_html( item['Local-Path'] ),
                related_page = parent_asset.related_page,
                parent       = parent_asset,
                child_number = 1,
                mime_type    = models.MimeType.HTML ))

        if not item['Is-New']:
            new_work.append(
                parent_asset.related_page.document.assets.get(
                    asset_class = models.AssetClass.DOCUMENT,
                    mime_type   = models.MimeType.BINARY ))

        if donomo.billing.models.expense('OCR', item['Owner']):
            return new_work
        else:
            raise Exception("Insufficient account balance")
            

    except OCRFailed:
        logging.warning('OCR failed, dropping from processing chain')

##############################################################################
