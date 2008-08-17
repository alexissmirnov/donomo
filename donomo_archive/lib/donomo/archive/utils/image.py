""" Image manipulation utilities
"""
import PIL.Image as Image
import os
from logging                   import getLogger

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
logging     = getLogger(MODULE_NAME)

###############################################################################
def make_thumbnail( original,
                    max_edge_length,
                    save_as = None,
                    format = 'JPEG'):
    """
    Create a thumbnail of the given original images, where the
    longest edge has max_edge_length, and the other edge is scaled
    accordingly.  If you specify a file name to save as, the resulting
    thumbnail will be written to disk.

    """
    logging.debug(
        'Creating thumbnail %s, save_as = %s' % (
            max_edge_length,
            save_as ))

    width, height = original.size

    if width > height:
        ratio = float( height ) / float( width )
        scale = ( max_edge_length,
                  int( ratio * max_edge_length) )
    else:
        ratio = float( width ) / float( height )
        scale = ( int( ratio * max_edge_length),
                  max_edge_length )

    new_image = original.copy()
    new_image.thumbnail(scale, Image.ANTIALIAS)

    if save_as:
        new_image.save(save_as, format)

    return new_image
