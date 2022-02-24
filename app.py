#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-02-24 14:51

@author: johannes
"""
from flask import Flask, render_template, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

import folium
from folium.plugins import FastMarkerCluster
from folium.plugins import Fullscreen

import os
import datetime
import pandas as pd

import cbs


app = Flask(__name__)

app.secret_key = '****************'

UPLOAD_FOLDER = './tmp'
ALLOWED_EXTENSIONS = {'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_register_frame(path):
    """Doc."""
    df = pd.read_csv(
        path,
        sep='\t',
        header=0,
        encoding='cp1252',
        dtype=str,
        keep_default_na=False,
    )

    floats = ['LATITUDE_WGS84_SWEREF99_DD', 'LONGITUDE_WGS84_SWEREF99_DD']
    df[floats] = df[floats].astype(float)
    df['SYNONYM_NAMES'] = df['SYNONYM_NAMES'].str.replace('<or>', '; ')
    return df.filter(
        ['LATITUDE_WGS84_SWEREF99_DD', 'LONGITUDE_WGS84_SWEREF99_DD',
         'STATION_NAME', 'REG_ID', 'REG_ID_GROUP', 'SYNONYM_NAMES',
         'OUT_OF_BOUNDS_RADIUS', 'LAT_DM', 'LONG_DM',
         'LATITUDE_SWEREF99TM', 'LONGITUDE_SWEREF99TM'],
        axis=1
    )


def get_template_stations(path):
    """Doc."""
    df = pd.read_excel(
        path,
        sheet_name='Provplatser',
        dtype=str,
        keep_default_na=False,
    )

    floats = ['Position WGS84 Dec N (DD.dddd)',
              'Position WGS84 Dec E (DD.dddd)']
    df[floats] = df[floats].astype(float)
    return df.filter(
        ['Position WGS84 Dec N (DD.dddd)', 'Position WGS84 Dec E (DD.dddd)',
         'Namn'],
        axis=1
    )


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('station_map', name=filename))
    return render_template('upload_file.html')


@app.context_processor
def inject_today_date():
    return {'year': datetime.date.today().year}


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/map')
def station_map(*args, **kwargs):
    df = get_register_frame('./data/station.txt')
    the_map = folium.Map(location=(60., 20.), zoom_start=5,
                         tiles='OpenStreetMap')
    fs = Fullscreen()
    folium.TileLayer('cartodbdark_matter').add_to(the_map)

    fmc = FastMarkerCluster(df.values.tolist(), callback=cbs.callback)
    fmc.layer_name = 'Register stations'

    fmc_rad = FastMarkerCluster(df.values.tolist(), callback=cbs.callback_rad)
    fmc_rad.layer_name = 'Register stations Radius'

    the_map.add_child(fmc)  # adding fastmarkerclusters to map
    the_map.add_child(fmc_rad)  # adding circle radius to map

    if any(os.scandir('./tmp')):
        tmp_path = os.path.join('./tmp', os.listdir('./tmp')[0])
        df_temp = get_template_stations(tmp_path)
        os.remove(tmp_path)
        fmc_tmp = FastMarkerCluster(df_temp.values.tolist(), callback=cbs.callback_tmps)
        fmc_tmp.layer_name = 'New stations'
        the_map.add_child(fmc_tmp)  # adding fastmarkerclusters to map

    the_map.add_child(fs)  # adding fullscreen button to map

    folium.LayerControl().add_to(the_map)  # adding layers to map
    return the_map._repr_html_()


if __name__ == '__main__':
    app.run(port=5000)
