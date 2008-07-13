
"""
The basic operations the can be performed on the document archive.  These
functions encapsulate all of the logic/management that goes into carrying
out these operations, including:

  - event logging
  - S3 uploads/downloads

"""

# ---------------------------------------------------------------------------

def upload( owner, data_stream, content_type ):
    """
    Upload a new object into the archive.
    """
    pass

# ---------------------------------------------------------------------------

def create_document( owner, title ):
    """
    Create a new document
    """
    pass

# ---------------------------------------------------------------------------

def add_page (document, data_stream, view_type):
    """
    Create a new page
    """
    pass

# ---------------------------------------------------------------------------

def split_document( document, at_page_number):
    """
    Split the given document into two documents, moving all pages starting
    from at_page_number and beyond into the new document.

    """
    pass

# ---------------------------------------------------------------------------

def merge_document( first, second):
    """
    Append the second document to the end of the first, removing the second
    doucment upon completion

    """
    pass

# ---------------------------------------------------------------------------

def move_page(
    initial_document,
    initial_position,
    final_document,
    final_position ):

    """
    Move a page from one document/position to another.

    """

    pass
