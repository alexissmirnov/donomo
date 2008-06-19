from __future__ import with_statement
from django.conf import settings
from docstore import log
from docstore.core import api as core_api
from docstore.core import utils as core_utils
from docstore.core.models import ViewType
from docstore.utils.path import path
from docstore.utils import run_system_command

import PIL.Image as Image
import os
import shutil

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
        try:
            handle_item(processor, item)
        except:
            log.exception('Failed to handle item')
    finally:
        core_api.close_work_item(item, True)

    return True

def handle_item(processor, item):
    local_path = path(item['Local-Path'])
    log.debug('processing %s' % local_path)

    document = item['Object'].document

    if not item['Content-Type'].startswith('image/tiff'):
        return

    # replace multipage .tif with a set of single-page .tif
    pages_path = local_path.dirname().joinpath(local_path.name + '.pages')
    pages_path.mkdir()
    log.debug('putting pages into %s' % pages_path)
    run_system_command('cd %s; tiffsplit ../%s' % (pages_path, local_path.name.replace('@','\@')))

    for tiff_page in pages_path.walkfiles('*.tif'):
        log.debug('processing %s' % tiff_page)

        # store a single page .tif for the purposes of OCR and a several JPEGs for
        # the purposes of the UI

        with open(tiff_page, 'rb') as tiff_page_file:
            page = core_api.create_page_with_initial_view(
                processor,
                processor.outputs.get(name = 'tiff-original'),
                document.owner,
                tiff_page_file)

        core_api.bind_page( document, page )

        # convert to JPEG via RGBA
        rgba_page      = pages_path.joinpath(path(tiff_page).name + '.rgba')
        jpeg_orig_path = pages_path.joinpath('%s.jpg' % path(tiff_page).name)
        jpeg_100_path  = pages_path.joinpath('%s-thumb-100.jpg' % path(tiff_page).name)
        jpeg_200_path  = pages_path.joinpath('%s-thumb-200.jpg' % path(tiff_page).name)

        run_system_command(
            'cd %s; tiff2rgba %s %s' % (
                pages_path,
                tiff_page,
                rgba_page.name))

        original = Image.open(rgba_page)
        thumb_100 = original.copy()
        thumb_200 = original.copy()

        width, height = original.size
        if width > height:
            ratio = float(height) / float(width)
            scale_100 = (100, int( ratio * 100.0))
            scale_200 = (200, int( ratio * 200.0))
        else:
            ratio = float(width) / float(height)
            scale_100 = (int( ratio * 100.0), 100)
            scale_200 = (int( ratio * 200.0), 200)

        thumb_100.thumbnail(scale_100, Image.ANTIALIAS)
        thumb_200.thumbnail(scale_200, Image.ANTIALIAS)

        original.save(jpeg_orig_path, 'JPEG')
        thumb_100.save(jpeg_100_path, 'JPEG')
        thumb_200.save(jpeg_200_path, 'JPEG')

        #
        # Upload the jpeg verisons of the page
        #

        with open(jpeg_orig_path, 'rb') as jpeg_file:
            log.info('Uploading %s ...' % jpeg_orig_path )
            core_api.create_page_view(
                processor,
                processor.outputs.get(name = 'jpeg-original'),
                page,
                jpeg_file )

        with open(jpeg_100_path, 'rb') as jpeg_file:
            log.info('Uploading %s ...' % jpeg_100_path )
            core_api.create_page_view(
                processor,
                processor.outputs.get(name = 'jpeg-thumbnail-100'),
                page,
                jpeg_file )


        with open(jpeg_200_path, 'rb') as jpeg_file:
            log.info('Uploading %s ...' % jpeg_200_path )
            core_api.create_page_view(
                processor,
                processor.outputs.get(name = 'jpeg-thumbnail-200'),
                page,
                jpeg_file )

    shutil.rmtree(pages_path)

    log.info('done. parsed tiffs for document %s by %s' % (
            document,
            document.owner))
