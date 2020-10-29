#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import multiprocessing
import pandas as pd
import numpy as np
import skimage
import gdal
import os

import solaris as sol
from solaris.raster.image import create_multiband_geotiff
from solaris.utils.core import _check_gdf_load


def map_wrapper(x):
    '''For multi-threading'''
    return x[0](*(x[1:]))


def make_geojsons_and_masks(name_root, image_path, json_path, 
                            output_path_mask, output_path_mask_fbc=None):
    print("  name_root:", name_root)

    # filter out null geoms (this is always a worthy check)
    gdf_tmp = _check_gdf_load(json_path)
    if len(gdf_tmp) == 0:
        gdf_nonull = gdf_tmp
    else:
        gdf_nonull = gdf_tmp[gdf_tmp.geometry.notnull()]
        try:
            im_tmp = skimage.io.imread(image_path)
        except:
            print("Error loading image %s, skipping..." %(image_path))
            return

    # handle empty geojsons
    if len(gdf_nonull) == 0:
        # create masks
        # mask 1 has 1 channel
        # mask_fbc has 3 channel
        print("    Empty labels for name_root!", name_root)
        im = gdal.Open(image_path)
        proj = im.GetProjection()
        geo = im.GetGeoTransform()
        im = im.ReadAsArray()
        # set masks to 0 everywhere
        mask_arr = np.zeros((1, im.shape[1], im.shape[2]))
        create_multiband_geotiff(mask_arr, output_path_mask, proj, geo)
        if output_path_mask_fbc:
            mask_arr = np.zeros((3, im.shape[1], im.shape[2]))
            create_multiband_geotiff(mask_arr, output_path_mask_fbc, proj, geo)
        return 
        
    # make masks (single channel)
    f_mask = sol.vector.mask.df_to_px_mask(df=gdf_nonull, out_file=output_path_mask,
                                     channels=['footprint'],
                                     reference_im=image_path,
                                     shape=(im_tmp.shape[0], im_tmp.shape[1]))
    
    # three channel mask (takes awhile)
    if output_path_mask_fbc:
        fbc_mask = sol.vector.mask.df_to_px_mask(df=gdf_nonull, out_file=output_path_mask_fbc,
                                     channels=['footprint', 'boundary', 'contact'],
                                     reference_im=image_path,
                                     boundary_width=5, contact_spacing=10, meters=True,
                                     shape=(im_tmp.shape[0], im_tmp.shape[1]))

    return

