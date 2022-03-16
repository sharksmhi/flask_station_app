#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-03-16 16:10

@author: johannes
"""
import numpy as np
from pyproj import CRS, transform


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
    lon_dd = 'Position WGS84 Dec E (DD.dddd)'
    lat_dd = 'Position WGS84 Dec N (DD.dddd)'
    floats = [lat_dd, lon_dd]
    if not df[lat_dd].any():
        if df['Position WGS84 DM N (DDMM.mm)'].any():
            df[lon_dd] = df['Position WGS84 DM E (DDMM.mm)'].apply(
                decmin_to_decdeg
            )
            df[lat_dd] = df['Position WGS84 DM N (DDMM.mm)'].apply(
                decmin_to_decdeg
            )
        elif df['Position SWEREF99 TM N (xxxxxx)'].any():
            x_array, y_array = convert_sweref99tm_2_wgs84(
                df['Position SWEREF99 TM N (xxxxxx)'].astype(float),
                df['Position SWEREF99 TM E (xxxxxx)'].astype(float)
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
    if 'Radie (m)' not in df:
        df['Radie (m)'] = 1200
    else:
        df['Radie (m)'] = [int(v) if v else 1200 for v in df['Radie (m)']]
