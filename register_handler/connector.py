#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-03-10 14:38

@author: johannes
"""
import os
import requests


VALID_ATTRIBUTES = {
    "local_id",
    "station_localid",
    "preferred_name",
    "responsible_datahost_name",
    "position_n", "position_sweref99_n",  # synonyms
    "position_e", "position_sweref99_e",  # synonyms
    "position_wgs84_dec_n",
    "position_wgs84_dec_e",
    "position_wgs84_dm_n",
    "position_wgs84_dm_e",
    "validated",
    "comment",
    "synonyms",
    "county_id",
    "older_site_id",
    "eu_cd",
    "associated_datahosts",
    "media",
    "facilityType",
    "classified",
    "sjoid_ri",
    "vdrid_ri",
    "sjoid_smhi_sjoregister"
}


def validate_data(data):
    """Check attributes of data.

    Delete attributes not found in VALID_ATTRIBUTES.
    """
    for key in list(data):
        if key not in VALID_ATTRIBUTES or not data[key]:
            del data[key]


class Connector:
    """Connect to the REST-API of the national station register."""

    @staticmethod
    def post(*args, data=None, **kwargs):
        """Post a new station.

        Create a new station and get ID back.
        """
        validate_data(data)
        resp = requests.request(
            "POST",
            url=os.getenv('APIURL'),
            json=data,
            headers={
                'Content-Type': 'application/json',
                'X-STNREG-APIKEY': os.getenv('APIKEY')
            },
        )
        return resp

    @staticmethod
    def put(*args, data=None, **kwargs):
        """Put and change station.

        Change a station attributes (eg. name, position, etc.).
        """
        raise NotImplementedError

    @staticmethod
    def delete(*args, **kwargs):
        """Delete a station.

        Erase a station from the national station register.
        """
        raise NotImplementedError
