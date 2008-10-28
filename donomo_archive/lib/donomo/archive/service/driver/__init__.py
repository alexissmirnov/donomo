from donomo.archive import operations

def init_processor(module):

    """ Private initialization function to get the processor object
        representing this service.

    """

    return operations.initialize_processor(
        module.__name__.rsplit('.', 1)[-1],
        module.DEFAULT_INPUTS,
        module.DEFAULT_OUTPUTS,
        module.DEFAULT_ACCEPTED_MIME_TYPES ) [0]

##############################################################################

def init_module( name ):
    """ Load and initialize a service module """
    module = __import__('donomo.archive.service.%s' % name, {}, {}, [''])
    return module


