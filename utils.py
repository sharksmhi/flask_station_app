#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-03-16 16:10

@author: johannes
"""
import yaml
import numpy as np
from pyproj import CRS, transform


with open(r'data\headers.yaml', encoding='cp1252') as fd:
    header_content = yaml.load(fd, Loader=yaml.FullLoader)


def decmin_to_decdeg(pos):
    """Convert coordinates.

    From degrees and decimal minutes into decimal degrees.
    """
    pos = float(pos.replace(',', '.').replace(' ', ''))
    return np.floor(pos / 100.) + (pos % 100) / 60.


def convert_sweref99tm_2_wgs84(lats, lons):
    """Convert coordinates from SWEREF99 TM into WGS84."""
    return transform(
        CRS('EPSG:3006'),
        CRS('EPSG:4326'),
        lons,
        lats,
        always_xy=True
    )


def eliminate_empty_rows(df):
    """Drop empty rows."""
    return df.loc[df.apply(any, axis=1), :].reset_index(drop=True)


def validate_coordinates(df):
    """Validate coordinates."""
    lon_dd = 'position_wgs84_dec_e'
    lat_dd = 'position_wgs84_dec_n'
    floats = [lat_dd, lon_dd]
    if not df[lat_dd].any():
        if df['position_wgs84_dm_n'].any():
            df[lon_dd] = df['position_wgs84_dm_e'].apply(
                decmin_to_decdeg
            )
            df[lat_dd] = df['position_wgs84_dm_n'].apply(
                decmin_to_decdeg
            )
        elif df['position_sweref99_n'].any():
            x_array, y_array = convert_sweref99tm_2_wgs84(
                df['position_sweref99_n'].astype(float),
                df['position_sweref99_e'].astype(float)
            )
            df[lon_dd] = x_array
            df[lat_dd] = y_array
        df[floats] = df[floats].round(6)
    else:
        for col in floats:
            df[col] = df[col].str.replace(',', '.')
        df[floats] = df[floats].astype(float)


def check_for_radius(df):
    """Check or add column for radius."""
    if 'radius' not in df:
        df['radius'] = 1200
    else:
        df['radius'] = [int(v) if v else 1200 for v in df['radius']]


class FileCommitter:
    def __init__(self):
        self._path = ''

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, p):
        self._path = p
