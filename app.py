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
import shutil
import sys
import glob
import functools
import datetime
import pandas as pd
import folium
from folium.plugins import FastMarkerCluster
from folium.plugins import Fullscreen
from werkzeug.utils import secure_filename
from threading import Thread
import requests
from io import StringIO

import cbs
import utils
from register_handler import Connector


PYTHON_VERSION = int(f'{sys.version_info.major}{sys.version_info.minor}')
UPLOAD_FOLDER = './tmp'
ALLOWED_EXTENSIONS = {'xlsx'}
VIEWS = ('Home', 'Search', 'Upload')


app = Flask(__name__)
app.secret_key = '****************'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

file_committer = utils.FileCommitter()
reg_connector = Connector()


def allowed_file(filename):
    """Return bool."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def reset_temporary_folder():
    """Reset the temporary folder."""
    today = datetime.date.today().strftime('%y%m%d')
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    else:
        for f in glob.glob('./tmp/*/'):
            if today not in f:
                shutil.rmtree(f)

    folder_today = os.path.join(UPLOAD_FOLDER, today)
    if not os.path.exists(folder_today):
        os.mkdir(folder_today)


def get_register_frame(raw=False):
    """Return dataframe.

    Read master station list (SODC).
    """
    # response = requests.request(
    #     "GET", "http://localhost:8005/getfile"
    # )

    # Store string data in a pandas Dataframe.
    df = pd.read_csv(
        # StringIO(response.text),
        r'data\station.txt',
        sep='\t',
        header=0,
        encoding='cp1252',
        dtype=str,
        keep_default_na=False,
    )
    df = df.rename(columns=utils.header_content['mapper'])
    if raw:
        return df
    else:
        floats = ['position_wgs84_dec_n', 'position_wgs84_dec_e']
        df[floats] = df[floats].astype(float)
        df['synonyms'] = df['synonyms'].str.replace('<or>', '; ')
        return df.filter(
            ['position_wgs84_dec_n', 'position_wgs84_dec_e',
             'preferred_name', 'local_id', 'station_localid', 'synonyms',
             'radius', 'position_wgs84_dm_n', 'position_wgs84_dm_e',
             'position_sweref99_n', 'position_sweref99_e'],
            axis=1
        )


def get_template_stations(path, filter_columns=True):
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
    df = df.rename(columns=utils.header_content['mapper'])
    df = utils.eliminate_empty_rows(df)
    utils.validate_coordinates(df)
    utils.check_for_radius(df)
    if filter_columns:
        return df.filter(['position_wgs84_dec_n', 'position_wgs84_dec_e',
                          'preferred_name', 'radius'], axis=1)
    else:
        return df


def get_folium_map(file_name=None):
    """Return folium a map object."""
    df = get_register_frame()
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

    if file_name:
        tmp_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            datetime.date.today().strftime('%y%m%d'),
            file_name
        )
        try:
            df_temp = get_template_stations(tmp_path)
            fmc_tmp = FastMarkerCluster(df_temp.values.tolist(),
                                        callback=cbs.callback_tmps)
            fmc_tmp.layer_name = 'New stations'
            fmc_tmp_rad = FastMarkerCluster(df_temp.values.tolist(),
                                            callback=cbs.callback_rad_tmps)
            fmc_tmp_rad.layer_name = 'New stations Radius'

            the_map.add_child(fmc_tmp)
            the_map.add_child(fmc_tmp_rad)
        except BaseException:
            pass

    the_map.add_child(fs)
    folium.LayerControl().add_to(the_map)
    return the_map


def get_layout_active_spec(name):
    """Return active layout spec."""
    return [
        {'name': n, 'class': "active" if n == name else "", 'href': n.lower()}
        for n in VIEWS
    ]


@app.context_processor
def inject_today_date():
    """Return current year."""
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


@app.route('/searcher', methods=['GET'])
@app.route('/station_app/searcher', methods=['GET'])
def search():
    """Search station from the main NODC list."""
    df = get_register_frame(raw=True)
    spec = get_layout_active_spec('Search')
    return render_template('searcher.html',
                           records=df.to_dict('records'),
                           active_spec=spec)


@app.route('/upload', methods=['GET', 'POST'])
@app.route('/station_app/upload', methods=['GET', 'POST'])
def upload():
    """Upload local file.

    Needs to follow the station register template.
    """
    spec = get_layout_active_spec('Upload')
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
            file.save(os.path.join(
                app.config['UPLOAD_FOLDER'],
                datetime.date.today().strftime('%y%m%d'),
                filename
            ))
            return render_template('upload_file.html',
                                   success=True,
                                   active_spec=spec,
                                   uploaded_file=filename)
    return render_template('upload_file.html', active_spec=spec)


@app.route('/submit', methods=['GET', 'POST'])
@app.route('/station_app/submit', methods=['GET', 'POST'])
def submit():
    """Upload local file.

    Needs to follow the station register template.
    """
    spec = get_layout_active_spec('Upload')
    if request.method == 'POST':
        filename = os.path.join(
            app.config['UPLOAD_FOLDER'],
            datetime.date.today().strftime('%y%m%d'),
            request.form.get('uploaded_file')
        )
        if filename:
            file_committer.path = filename
            df = get_template_stations(filename, filter_columns=False)
            return render_template('upload_file.html',
                                   active_spec=spec,
                                   header_upload=list(df.columns),
                                   data_upload=df.to_dict('records'),
                                   connect_to_reg=True)

    return render_template('upload_file.html', active_spec=spec)


@app.route('/commit_to_reg', methods=['GET'])
@app.route('/station_app/commit_to_reg', methods=['GET'])
def commit_to_reg():
    """Send stations to the national station register."""
    spec = get_layout_active_spec('Upload')
    if file_committer.path:
        df = get_template_stations(file_committer.path, filter_columns=False)
        data_list = df.to_dict('records')
        for i, statn_dict in enumerate(data_list):
            resp = reg_connector.post(data=statn_dict)
            if resp.status_code == 201:
                resp_data = resp.json()
                df['local_id'][i] = resp_data.get('localid')
                df['station_localid'][i] = resp_data.get('station_localid')
            elif resp.status_code == 409:
                resp_data = resp.json()
                df['local_id'][i] = resp_data.get('localid')
            else:
                print('resp.status_code', resp.status_code)

        return render_template('upload_file.html',
                               active_spec=spec,
                               header_upload=list(df.columns),
                               data_upload=df.to_dict('records'),
                               connect_to_reg=True)
    return render_template('upload_file.html', active_spec=spec)


@app.route('/map')
@app.route('/station_app/map')
def station_map():
    """Return html page based on a folium map."""
    map_obj = get_folium_map(file_name=request.args.get('uploaded_file'))
    return map_obj._repr_html_()


@app.route('/')
@app.route('/station_app/')
def home():
    """Return html page from template."""
    Thread(target=reset_temporary_folder).start()
    spec = get_layout_active_spec('Home')
    return render_template('home.html', active_spec=spec)


if __name__ == '__main__':
    app.run(port=5000)
