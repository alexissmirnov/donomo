#!/usr/bin/env python

""" Helper script to run a process on an asset
"""

from donomo.archive         import models
from donomo.archive         import operations
from donomo.archive.service import driver

import logging
import sys
import os
import shutil

def main():
    """ Run the process on the given asset where both the process and the
        asset id are given on the command line.
    """
    try:
        name     = sys.argv[1]
        asset_id = sys.argv[2]

        module    = driver.init_module(name)
        processor = driver.init_processor(module)
    
        work_item = {
            'Process-Name' : name,
            'Asset-ID'     : asset_id,
            }
        
        try:
            work_item.update(operations.instantiate_asset(asset_id))
        except models.Asset.DoesNotExist:
            logging.exception('Failed to instantiate asset: %s' % asset_id)
        else:
            module.handle_work_item(processor, work_item)
            
    except:
        logging.exception('Failed to run processor')
        sys.exit(1)

    finally:
        local_path = work_item.get('Local-Path')
        if local_path and os.path.exists(local_path):
            shutil.rmtree(os.path.dirname(local_path))

if __name__ == '__main__':
    main()

