#!/usr/bin/env python

""" Helper script to run a process on an asset
"""

from donomo.archive         import models
from donomo.archive         import operations
from donomo.archive.service import driver, NotReadyException
from django.db              import transaction
from boto.exception         import S3ResponseError
import logging
import sys
import os
import shutil

@transaction.commit_on_success
def handle_work_item(module, processor, work_item):
    """ Wrapper to put the execution of the processor in a transaction.
    """
    module.handle_work_item(processor, work_item)

def main():
    """ Run the process on the given asset where both the process and the
        asset id are given on the command line.
    """
    try:
        name     = sys.argv[1]
        asset_id = sys.argv[2]
        is_new   = int(sys.argv[3]) != 0

        work_item = {
            'Process-Name' : name,
            'Asset-ID'     : asset_id,
            'Is-New'       : is_new,
            }

        module    = driver.init_module(name)
        processor = driver.init_processor(module)


        try:
            work_item.update(operations.instantiate_asset(asset_id))
        except models.Asset.DoesNotExist:
            logging.error('Asset no longer exists: %s' % asset_id)
        except S3ResponseError, error:
            if error.status == 404:
                logging.error('Could not find asset in S3: %s' % asset_id)
            else:
                logging.exception('Unexpected error!')
                raise
        else:
            handle_work_item(module, processor, work_item)

    except NotReadyException, e:
        logging.info(e)
        sys.exit(1)

    except:
        logging.exception('Failed to run processor')
        sys.exit(1)

    finally:
        local_path = work_item.get('Local-Path')
        if local_path and os.path.exists(local_path):
            shutil.rmtree(os.path.dirname(local_path))

if __name__ == '__main__':
    main()

