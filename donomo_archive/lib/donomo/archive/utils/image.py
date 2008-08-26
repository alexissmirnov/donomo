"""
Heper utility to generate thumbnail images
"""

from PIL import Image, ImageFilter, ImageChops

##############################################################################

def open( path ):

    """ Open the image located at path.
    """

    return Image.open(path)

##############################################################################

def save( image, path ):
    """ Save the given image to the given path
    """

    image.save(path, 'JPEG', quality=95)

##############################################################################

def trim( image ):

    """ Return a copy of the original image with excess whitespace
        removed.

    """

    # Create black and white version of the image
    two_tone = image.convert('1')
    two_tone = two_tone.filter(ImageFilter.MedianFilter)

    # Create a white background the same size as the image
    white = Image.new('1', image.size, 255)

    # Compare the two images and get a bounding box for the differences.
    diff = ImageChops.difference(two_tone, white)
    bbox = diff.getbbox()

    # Crop the image to the bounding box, if any
    if bbox:
        image = image.crop(bbox)

    # we're done
    return image

###############################################################################

def thumbnail( image, size ):

    """ Create a thumbnail of the given image that fits into a box
        having the dimentions given in size (a tuple: width, height).

    """

    # Trim whitespace around image
    image = trim(image)

    # Calculate scaling ratio to get image to fit into the given size
    width, height         = [float(v) for v in image.size]
    new_width, new_height = [float(v) for v in size]
    ratio                 = min( new_width / width, new_height / height )

    # Scale the image to the new size
    image = image.resize(
        settings.THUMBNAIL_SIZE,
        resample = Image.ANTIALIAS)

    # Apply light sharpening to bring out the details
    image = image.filter(ImageFilter.DETAIL)

    return image

##############################################################################
