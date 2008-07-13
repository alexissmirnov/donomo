""" Image manipulation utilities
"""
import PIL.Image as Image


def make_thumbnail(original, th_width, output_path, format = 'JPEG'):
    """Produces a file in given path having the same aspect 
    ratio as the original, with
    its width set to th_width, with given format
    """
    thumb = original.copy()
    width, height = original.size
    if width > height:
        ratio = float(height) / float(width)
        scale = (th_width, int( ratio * float(th_width)))
    else:
        ratio = float(width) / float(height)
        scale = (int( ratio * float(th_width)), th_width)

    thumb.thumbnail(scale, Image.ANTIALIAS)
    thumb.save(output_path, format)
    return thumb