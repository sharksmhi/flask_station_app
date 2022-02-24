#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-02-24 14:51

@author: johannes
"""

callback = (
        'function (row) {'
        'var marker = L.marker(new L.LatLng(row[0], row[1]));'
        'var icon = L.AwesomeMarkers.icon({'
        "icon: 'map-marker',"
        "markerColor: 'blue',"
        '});'
        'marker.setIcon(icon);'
        'marker.bindTooltip(row[2], {direction: "top"});'
        'L.circle([row[0], row[1]], {radius: 1000});'
        "var popup = L.popup({maxWidth: '300'});"
        "const display_text = {text: '<b>Station: </b>' + row[2] + '</br>' + '<b> ID: </b>' + row[3] + '</br>' + '<b> ID group: </b>' + row[4] + '</br>' + '<b> Synonyms: </b>' + row[5] + '</br>' + '<b> Radius: </b>' + row[6] + '</br>' + '<b> Lat (DD): </b>' + row[0] + '</br>' + '<b> Lon (DD): </b>' + row[1] + '</br>' + '<b> Lat (DM): </b>' + row[7] + '</br>' + '<b> Lon (DM): </b>' + row[8] + '</br>' + '<b> Lat sweref99tm: </b>' + row[9] + '</br>' + '<b> Lon sweref99tm: </b>' + row[10]};"
        "var mytext = $(`<div id='mytext' class='display_text' style='width: 100.0%; height: 100.0%;'> ${display_text.text}</div>`)[0];"
        "popup.setContent(mytext);"
        "marker.bindPopup(popup);"
        'return marker};'
)

callback_rad = (
    'function (row) {'
    'var circle = L.circle([row[0], row[1]], {radius: row[6], fill_color: "#3186cc", weight: 0.5});'
    'return circle};'
)


callback_tmps = (
        'function (row) {'
        'var marker = L.marker(new L.LatLng(row[0], row[1]));'
        'var icon = L.AwesomeMarkers.icon({'
        "icon: 'map-marker',"
        "markerColor: 'red',"
        '});'
        'marker.setIcon(icon);'
        'marker.bindTooltip(row[2], {direction: "top"});'
        "var popup = L.popup({maxWidth: '300'});"
        "const display_text = {text: '<b>Station: </b>' + row[2] + '</br>' + '<b> Lat (DD): </b>' + row[0] + '</br>' + '<b> Lon (DD): </b>' + row[1]};"
        "var mytext = $(`<div id='mytext' class='display_text' style='width: 100.0%; height: 100.0%;'> ${display_text.text}</div>`)[0];"
        "popup.setContent(mytext);"
        "marker.bindPopup(popup);"
        'return marker};'
)
