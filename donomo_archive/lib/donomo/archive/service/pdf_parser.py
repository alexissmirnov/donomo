"""
PDF Process Driver. 
Input:
One multi-page PDF

Types of PDFs supported:
 - one-image per page, no text -- eg. the kind that comes out from 
     ScanSnap scanner
Output:
 - A set of images, one image per page.
 - JPEG thumbnails for each page
 
 Environement setup:
 The following programs must be in the PATH:
 pdftk (pdf splitter)
 gs (ghostscript)
 convert (imagemagick)
 
env vars:
MAGICK_HOME=/usr/local/ImageMagick-6.4.1
DYLD_LIBRARY_PATH=$MAGICK_HOME/lib

 
"""
from __future__                 import with_statement
from donomo.archive.utils       import pdf
from logging                    import getLogger
from donomo.archive.utils       import path, image

from docstore.core import api as core_api

import PIL.Image as Image

log = getLogger('PDF')

DEFAULT_OUTPUTS = (
    ( 'tiff-original',      'image/tiff', ['docstore.processor.ocr']),
    ( 'jpeg-original',      'image/jpeg', []),
    ( 'jpeg-thumbnail-100', 'image/jpeg', []),
    ( 'jpeg-thumbnail-200', 'image/jpeg', []),
    )

def get_processor():
    return core_api.get_or_create_processor(__name__, DEFAULT_OUTPUTS)

def run_once():
    processor = get_processor()

    #log.debug('getting next work item for processor %s' % processor)

    item = core_api.get_work_item(processor, 0)

    if item is None:
        return False


    try:
        handle_work_item(processor, item)
        core_api.close_work_item(item, True)
        return True
    except:
        log.exception('Failed to handle item')
        raise
    
    return False

def handle_work_item(processor, item):
        """
        Process a work item.  The work item will be provided and its
        local temp file will be cleaned up by the process driver
        framework.  If this method returns true, the work item will
        also be removed from the work queue.

        """
        local_path = item['Local-Path']
        document = item['Object'].document

        # split a PDF into one-page PDF files
        pages_output_dir = pdf.split(local_path)
        
        # iterate over all *.pdf files in the output directory and
        # convert each page to a image file (change TIFF to 
        # PNG when OCR is ready)
        #map(lambda x: pdf.convert(x, 'tiff'), output_dir.listdir('*.pdf'))

        for page_pdf in pages_output_dir.listdir('*.pdf'):
            log.debug('processing %s' % page_pdf)
            
            # create TIFF page
            page_tiff = pdf.convert(page_pdf, 'tiff')
            with open(page_tiff, 'rb') as tiff_page_file:
                page = core_api.create_page_with_initial_view(
                    processor,
                    processor.outputs.get(name = 'tiff-original'),
                    document.owner,
                    tiff_page_file)
    
            core_api.bind_page( document, page )
            
            # create full-size JPEG
            page_jpg = pdf.convert(page_pdf, 'jpg')
            with open(page_jpg, 'rb') as jpeg_file:
                log.info('Uploading %s ...' % page_jpg )
                core_api.create_page_view(
                    processor,
                    processor.outputs.get(name = 'jpeg-original'),
                    page,
                    jpeg_file )
                
            original = Image.open(page_jpg)  
            
            # create 100px thumbnail
            page_th100_jpg = pages_output_dir.joinpath('%s-thumb-100.jpg' % page_jpg.namebase)
            image.make_thumbnail(original, 100, page_th100_jpg)
            with open(page_th100_jpg, 'rb') as jpeg_file:
                log.info('Uploading %s ...' % page_th100_jpg )
                core_api.create_page_view(
                    processor,
                    processor.outputs.get(name = 'jpeg-thumbnail-100'),
                    page,
                    jpeg_file )

            # create 200px thumbnail
            page_th200_jpg = pages_output_dir.joinpath('%s-thumb-200.jpg' % page_jpg.namebase)
            image.make_thumbnail(original, 200, page_th200_jpg)
            with open(page_th200_jpg, 'rb') as jpeg_file:
                log.info('Uploading %s ...' % page_th200_jpg )
                core_api.create_page_view(
                    processor,
                    processor.outputs.get(name = 'jpeg-thumbnail-200'),
                    page,
                    jpeg_file )
    
        
        # delete all temporary files  
        pages_output_dir.rmtree()
        return True
    