#!/usr/bin/env python

from donomo.archive.models import *

def setup_sub_assets(asset, level):
    print '  ' * level, asset
    for asset_class in AssetClass.objects.all():
        number = 0
        for child in asset.children.filter(asset_class = asset_class).order_by( 'id' ):
            number += 1
            child.child_number = number
            child.save()
            setup_sub_assets(child, level + 1)

def update_asset_tree():
    for asset in Asset.objects.filter( parent__isnull=True ):
        setup_sub_assets(asset, 0)
