#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-02-24 14:51

@author: johannes
"""
import flask
from flask import (
    Flask,
    render_template,
    flash,
    request,
    redirect,
    url_for
)
import os
import sys
import datetime
import pandas as pd
import folium
from folium.plugins import FastMarkerCluster
from folium.plugins import Fullscreen
from werkzeug.utils import secure_filename

import cbs


PYTHON_VERSION = int(f'{sys.version_info.major}{sys.version_info.minor}')
UPLOAD_FOLDER = './tmp'
ALLOWED_EXTENSIONS = {'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app = Flask(__name__)
app.secret_key = '****************'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """Return bool."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_register_frame(path):
    """Return dataframe.

    Read master station list (SODC).
    """
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
    """Return dataframe.

    Read excel template with new stations.
    """
    df = pd.read_excel(
        path,
        sheet_name='Provplatser',
        dtype=str,
        keep_default_na=False,
        engine=None if PYTHON_VERSION >= 37 else 'openpyxl'
    )

    floats = ['Position WGS84 Dec N (DD.dddd)',
              'Position WGS84 Dec E (DD.dddd)']
    df[floats] = df[floats].astype(float)
    return df.filter(
        ['Position WGS84 Dec N (DD.dddd)', 'Position WGS84 Dec E (DD.dddd)',
         'Namn'],
        axis=1
    )


def get_folium_map():
    """Return folium a map object."""
    df = get_register_frame('./data/station.txt')
    the_map = folium.Map(location=(60., 20.), zoom_start=5,
                         tiles='OpenStreetMap')
    fs = Fullscreen()
    folium.TileLayer('cartodbdark_matter').add_to(the_map)

    fmc = FastMarkerCluster(df.values.tolist(), callback=cbs.callback)
    fmc.layer_name = 'Register stations'

    fmc_rad = FastMarkerCluster(df.values.tolist(), callback=cbs.callback_rad)
    fmc_rad.layer_name = 'Register stations Radius'

    the_map.add_child(fmc)
    the_map.add_child(fmc_rad)

    if any(os.scandir('./tmp')):
        tmp_path = os.path.join('./tmp', os.listdir('./tmp')[0])
        df_temp = get_template_stations(tmp_path)
        os.remove(tmp_path)
        fmc_tmp = FastMarkerCluster(df_temp.values.tolist(),
                                    callback=cbs.callback_tmps)
        fmc_tmp.layer_name = 'New stations'
        the_map.add_child(fmc_tmp)

    the_map.add_child(fs)
    folium.LayerControl().add_to(the_map)
    return the_map


@app.context_processor
def inject_today_date():
    """Retrun current year."""
    return {'year': datetime.date.today().year}


@app.route('/cover.css', methods=['GET'])
@app.route('/station_app/cover.css', methods=['GET'])
def get_cover_css():
    with open('static/css/cover.css') as f:
        content = f.read()
        response = flask.Response(content)
        response.headers['Content-Type'] = 'text/css'
        return response


@app.route('/dm_map.png', methods=['GET'])
@app.route('/station_app/dm_map.png', methods=['GET'])
def get_bg_image():
    with open('static/images/dm_map.png', mode='rb') as f:
        content = f.read()
        response = flask.Response(content)
        response.headers['Content-Type'] = 'image/png'
        return response


@app.route('/upload', methods=['GET', 'POST'])
@app.route('/station_app/upload', methods=['GET', 'POST'])
def upload_file():
    """Upload local file.

    Needs to follow the station register template.
    As of right now, lat/long in DD-format is mandatory.
    """
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


@app.route('/')
@app.route('/station_app/')
def home():
    """Return html page from template."""
    return render_template('home.html')


@app.route('/map')
@app.route('/station_app/map')
def station_map():
    """Return html page based on a folium map."""
    map_obj = get_folium_map()
    return map_obj._repr_html_()


if __name__ == '__main__':
    app.run(port=5000)
