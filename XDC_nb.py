
# -*- coding: utf-8 -*-

# Copyright 2018 Spanish National Research Council (CSIC)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import datetime
import warnings
from datetime import timedelta
from datetime import datetime
from dateutil import parser
import numpy as np
from numpy.ma import masked_inside, masked_outside
import os
import shutil
import requests
import json
from netCDF4 import Dataset
from typing import overload
import re

# import model submodules
from wq_modules import modeling_file

# import meteo submodules
from wq_modules import meteo

# import general submodules
from wq_modules import utils
from wq_modules import config

# widget
import ipywidgets as widgets
from ipywidgets import HBox, VBox, Layout
from IPython.display import display
from IPython.display import clear_output

# Eliminar warnings
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

warnings.filterwarnings("ignore")


def plot_meteo(region_buttons, ini_date, end_date, actions):
    region = region_buttons.value
    sd = ini_date.value
    # datetime.strptime(ini_date.value, "%m-%d-%Y")
    ed = end_date.value
    m = meteo.Meteo(sd, ed, region)
    m.params = ["ID", "Date", "Temp"]
    meteo_output = m.get_meteo()
    data = pd.read_csv(meteo_output['output'], delimiter=';', decimal=',')
    data['Date'] = pd.to_datetime(data['Date'])
    # data["Temp"] = float(data["Temp"])
    data
    data.plot(x='Date', y='Temp')
    plt.show()


def plot_satellite(region_buttons, ini_date, end_date, actions):

    # Check the format date and if end_date > start_date
    st_date = ini_date.value
    ed_date = end_date.value
    sd, ed = utils.valid_date(st_date, ed_date)

    # chek the region to attach coordinates
    region = region_buttons.value
    utils.valid_region(region)

    # check if the action exist in the Keywords list of config file
    act = actions.value[0]
    utils.valid_action(act)

    # Configure the tree of the temporal datasets path.
    # Create the folder and the downloaded_files file
    onedata_mode = config.onedata_mode
    utils.path_configurations(onedata_mode)


def find_dataset_type(start_date, end_date, typ, onedata_token):
    headers = {"X-Auth-Token": onedata_token}
    url = ("https://cloud-90-147-75-163.cloud.ba.infn.it"
           "/api/v3/oneprovider/spaces/17d670040b30511bc4848cab56449088")
    r = requests.get(url, headers=headers)
    space_id = json.loads(r.content)['spaceId']
    print('Onedata space ID: %s' % space_id)
    index_name = 'region_type__query'
    # onedata_cdmi_api = ("https://cloud-90-147-75-163.cloud.ba.infn.it"
    #                    "/cdmi/cdmi_objectid/")
    url = "https://cloud-90-147-75-163.cloud.ba.infn.it/api/v3"
    url = url + "/oneprovider/spaces/"
    url = url + space_id + "/indexes/" + index_name + "/query"
    r = requests.get(url, headers=headers)
    response = json.loads(r.content)
    result = []
    for e in response:
        if typ in e['key']['dataset']:
            print(e['key']['dataset'])
            if check_date(
                start_date,
                end_date,
                e['key']['beginDate'],
                e['key']['endDate']):
                print({
                    'beginDate': e['key']['beginDate'],
                    'endDate': e['key']['endDate'],
                    'file': e['key']['dataset']
                })
                result.append({
                    'beginDate': e['key']['beginDate'],
                    'endDate': e['key']['endDate'],
                    'file': e['key']['dataset']
                })
    return result


def find_models(onedata_token):
    headers = {"X-Auth-Token": onedata_token}
    url = ("https://cloud-90-147-75-163.cloud.ba.infn.it"
           "/api/v3/oneprovider/spaces/17d670040b30511bc4848cab56449088")
    r = requests.get(url, headers=headers)
    space_id = json.loads(r.content)['spaceId']
    print('Searching models')
    index_name = 'models_region_query'
    # onedata_cdmi_api = ("https://cloud-90-147-75-163.cloud.ba.infn.it" +
    #                     + "/cdmi/cdmi_objectid/")
    url = ("https://cloud-90-147-75-163.cloud.ba.infn.it"
           "/api/v3/oneprovider/spaces/%s/indexes/%s/query" % (
               space_id, index_name))
    r = requests.get(url, headers=headers)
    response = json.loads(r.content)
    return response


def is_downloaded(onedata_token, filename):
    headers = {"X-Auth-Token": onedata_token}
    url = ("https://vm027.pub.cloud.ifca.es"
           "/api/v3/oneprovider/spaces/ecf6abbd4fcd6d6c9b505d5f5e82f94c")
    r = requests.get(url, headers=headers)
#    space_id = json.loads(r.content)['spaceId']
    space_id= 'ecf6abbd4fcd6d6c9b505d5f5e82f94c'
    index_name = 'filename'

    if index_name not in list_onedata_views(onedata_token):
        create_filename_view(onedata_token)
    url = ("https://vm027.pub.cloud.ifca.es"
           "/api/v3/oneprovider/spaces/%s/views/%s/query?spatial=false&stall=false" % (
               space_id, index_name))
    r = requests.get(url, headers=headers)
    response = json.loads(r.content)

    result = False

    if len(response) == 0:
        return result
    elif len(response) == 1:
        response = response[0]['key']
    elif len(response) == 2:
        response = response[0]['key'] + response[1]['key']

    if filename in response:
        result = True

    return result


#date is a string yyyy-mm-dd
def find_closest_date(onedata_token, date, region):

    headers = {"X-Auth-Token": onedata_token}

    date_time_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
    seconds_since_epoch = date_time_obj.timestamp()
    seconds_since_epoch = int(seconds_since_epoch)*1000

    space_id = 'ecf6abbd4fcd6d6c9b505d5f5e82f94c'

    index_name = 'view_date_landsat'
    if index_name not in list_onedata_views(onedata_token):
        create_landsat_date_view(onedata_token)

    url = ("https://vm027.pub.cloud.ifca.es"
           "/api/v3/oneprovider/spaces/%s/views/%s/query?spatial=false&stall=false" % (
               space_id, index_name))
    r = requests.get(url, headers=headers)
    value = ''
    min = 999999999999999
    for e in json.loads(r.content):
        if e['value'][0] == region:
            if min > abs(seconds_since_epoch - e['key']):
                min = abs(seconds_since_epoch - e['key'])
                value = e['value'][1]

    return value


def list_onedata_views(onedata_token):
    headers = {"X-Auth-Token": onedata_token}
    space_id = "ecf6abbd4fcd6d6c9b505d5f5e82f94c"
    url = ("https://vm027.pub.cloud.ifca.es"
       "/api/v3/oneprovider/spaces/%s/views/" %
           space_id)
    r = requests.get(url, headers=headers)
    return json.loads(r.content)["views"]


def create_filename_view(onedata_token):
    headers = {"X-Auth-Token": onedata_token}
    url = ("https://vm027.pub.cloud.ifca.es"
           "/api/v3/oneprovider/spaces/ecf6abbd4fcd6d6c9b505d5f5e82f94c")
    r = requests.get(url, headers=headers)
#    space_id = json.loads(r.content)['spaceId']
    space_id= 'ecf6abbd4fcd6d6c9b505d5f5e82f94c'
    data = open('/wq_sat/views/view_filename.js','rb')
    print ('data_ {}'.format(data))
    print('Searching models')
    index_name = 'filename'
    url = ("https://vm027.pub.cloud.ifca.es"
           "/api/v3/oneprovider/spaces/%s/views/%s?spatial=false" % (
               space_id, index_name))
    r = requests.put(url, data = data, headers = headers)
    return r.status_code


def create_landsat_date_view(onedata_token):
    headers = {"X-Auth-Token": onedata_token}
    url = ("https://vm027.pub.cloud.ifca.es"
           "/api/v3/oneprovider/spaces/ecf6abbd4fcd6d6c9b505d5f5e82f94c")
    r = requests.get(url, headers=headers)
    space_id = 'ecf6abbd4fcd6d6c9b505d5f5e82f94c'
    data = open('/wq_sat/views/view_dates_landsat.js','rb')
    index_name = 'view_date_landsat'
    url = ("https://vm027.pub.cloud.ifca.es"
           "/api/v3/oneprovider/spaces/%s/views/%s?spatial=false" % (
               space_id, index_name))
    r = requests.put(url, data = data, headers = headers)
    return r.status_code


def model_temp(onedata_token, date, region):

    l8_file = find_closest_date(onedata_token, date, region)
    file_path = os.path.join(config.datasets_path, region, l8_file)
    dataset= Dataset(file_path, 'r', format='NETCDF4_CLASSIC')
    variables = dataset.variables

    G = dataset.variables['SRB3'][:]
    NIR = dataset.variables['SRB5'][:]

    mndwi = (G - NIR) / (G + NIR)
    mndwi[mndwi <=0] = np.nan
    mndwi = np.ma.masked_where(condition=np.isnan(mndwi), a=mndwi)

    B11 = dataset.variables['SRB11'][:]
    B11[mndwi.mask] = np.nan
    B11 = np.ma.masked_where(condition=np.isnan(B11), a=B11)
    Temp = np.mean(B11) - 273.15

    return Temp


def check_date(start_date, end_date, meta_beginDate, meta_endDate):
    meta_start_date = parser.parse(meta_beginDate)
    meta_end_date = parser.parse(meta_endDate)
    try:
        print("Slctd[st: %s end: %s ]|Meta:[st: %s end: %s]" % (
            start_date,
            end_date,
            meta_start_date,
            meta_end_date))
        if meta_start_date.date() <= start_date and \
            meta_end_date.date() >= end_date:
            print("Candidate File")
            return True
        elif meta_start_date.date() == meta_end_date.date() and \
            meta_start_date.date() >= start_date and \
            meta_end_date.date() <= end_date:
            print("Candidate File")
            return True
        else:
            return False
    except ValueError:
        print("Wrong Date format")
        return False


def prepare_model(start_date, end_date, region, path, onedata_token):
    # Parameters
    ini_date_str = start_date.strftime('%Y-%m-%d') + ' 00:00:00'
    end_date_str = end_date.strftime('%Y-%m-%d') + ' 00:00:00'

    print(("Generating new model" + '/model_%s_%s/' % (
        (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))))
    try:
        shutil.copytree(
            "%s%s/model" % (path, region),
            "%s%s/model_%s_%s/" % (
                path, region,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')))

    except FileExistsError:
        shutil.rmtree("%s%s/model_%s_%s/" % (
            path, region, start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')))
        shutil.copytree(
            "%s%s/model" % (path, region),
            "%s%s/model_%s_%s/" % (
                path, region,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')))
    base_path = "%s%s/model_%s_%s/" % (
        path, region, start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d'))
    fmt = '%Y-%m-%d %H:%M:%S'
    ini_date = datetime.strptime(ini_date_str, fmt)
    end_date = datetime.strptime(end_date_str, fmt)

    f1 = open(base_path + 'test_1.mdf', 'r')
    f2 = open(base_path + 'test_1_v2.mdf', 'w')

    # Layers
    # k = 35
    print(modeling_file.minutes_between_date(ini_date, end_date))

    # Check Wind file

    wind_input = ''
    # Search once. If it is not found, it tries to download the data
    try:
        print("Searching Wind data")
        wind_input = (
            path + region + '/' + find_dataset_type(
                ini_date.date(), end_date.date(),
                'wind', onedata_token)[0]["file"])
    except Exception as e:
        print(e)
        print("Getting data")
        m = meteo.Meteo(ini_date.date(), end_date.date(), region)
        m.params = ["ID", "date", "speed", "dir"]
        wind_input = m.get_meteo()['output']
    # Second time. If it is not found, it generates a generic file.
    try:
        if wind_input == '':
            print("Searching Wind data again")
            wind_input = (
                path + region + '/' + find_dataset_type(
                    ini_date.date(), end_date.date(), 'wind',
                    onedata_token)[0]["file"])
    except Exception:
        wf = open(base_path + 'wind_generic.csv', 'w')
        line = (
            "date;speed;dir\n\"%s\";2.72;277\n\"%s\";2.72;277\n" % (
                ini_date_str, end_date_str))
        wf.write(line)
        wf.close()
        wind_input = base_path + 'wind_generic.csv'

    print("Creating file .wnd from CSV: %s" % wind_input)
    wind_file_name = "wind_%s_%s.wnd" % (
        ini_date.strftime('%Y-%m-%d%H%M%S'),
        end_date.strftime('%Y-%m-%d%H%M%S'))
    modeling_file.csv_to_wind(
        wind_input, ini_date, end_date, base_path + wind_file_name)
    print("Wind file created: %s" % wind_file_name)

    # Check initial conditions
    # TODO For the moment, only with uniform values
    print("Searching Initial data")
    print("Getting initial data")
    print("Creating initial data file .ini")
    ini_file_name = "initial_%s_%s.ini" % (
        ini_date.strftime('%Y-%m-%d%H%M%S'),
        end_date.strftime('%Y-%m-%d%H%M%S'))
    print("Initial file created: %s" % ini_file_name)
    # Check Radiation file
    print("Searching Radiation data")
    print("Getting data")
    try:
        rad_input = path + find_dataset_type(
            ini_date.date(), end_date.date(), 'rad', onedata_token)[0]['file']
    except Exception:
        rf = open(base_path + 'rad_generic.csv', 'w')
        line = ("date;hum;temp;rad\n\"%s\";22.72"
                ";12.4;0\n\"%s\";22.72;12.4;200\n" % (
                    ini_date_str, end_date_str))
        rf.write(line)
        rf.close()
        rad_input = base_path + 'rad_generic.csv'
    print("Creating file .tem")
    rad_file_name = "rad_%s_%s.tem" % (
        ini_date.strftime('%Y-%m-%d%H%M%S'),
        end_date.strftime('%Y-%m-%d%H%M%S'))
    modeling_file.csv_to_tem(
        rad_input, ini_date, end_date, base_path + rad_file_name)
    print("Radiation file created: %s" % rad_file_name)

    # Input-Output flow
    print("Searching flow data")
    print("Getting data")

    # Uniform output
    out_dic = {
        1: {
            'Name': 'Presa',
            'Flow': 0.5
        }
    }
    presa_bct = 'Presa.bct'
    # input_csv = 'data/'
    # csv_to_bct(out_dic, presa_bct,input_csv,ini_date,end_date)
    modeling_file.gen_uniform_output_bct(
        out_dic, base_path + presa_bct, ini_date, end_date)

    out_dic = {
        1: {
            'Name': 'Presa',
            'Temperature': 12.5,
            'Salinity': 0.03
        }
    }
    presa_bcc = 'Presa.bcc'
    modeling_file.gen_uniform_output_bcc(
        out_dic, base_path + presa_bcc, ini_date, end_date)

    input_dic = {
        1: {
            'Name': 'Duero',
            'Flow': 0.4,
            'Temperature': 12.5,
            'Salinity': 0.03
        },
        2: {
            'Name': 'Revinuesa',
            'Flow': 0.4,
            'Temperature': 12.5,
            'Salinity': 0.03
        },
        3: {
            'Name': 'Ebrillos',
            'Flow': 0.4,
            'Temperature': 12.5,
            'Salinity': 0.03
        },
        4: {
            'Name': 'Dehesa',
            'Flow': 0.4,
            'Temperature': 12.5,
            'Salinity': 0.03
        },
        5: {
            'Name': 'Remonicio',
            'Flow': 0.4,
            'Temperature': 12.5,
            'Salinity': 0.03
        }
    }
    input_dis = 'tributaries.dis'
    modeling_file.gen_uniform_intput_dis(
        input_dic, base_path + input_dis, ini_date, end_date)

    # Parameters update
    dic = {
        'Itdate': "#" + ini_date.strftime('%Y-%m-%d') + "#\n",
        'Tstart': "%i\n" % modeling_file.minutes_between_date(
            datetime.strptime(
                ini_date.strftime('%Y-%m-%d'), '%Y-%m-%d'), ini_date),
        'Tstop': "%i\n" % modeling_file.minutes_between_date(
            ini_date, end_date),
        'Filwnd': "#" + wind_file_name + "#\n",
        'Filtmp': "#" + rad_file_name + "#\n",
        'FilbcT': "#" + presa_bct + "#\n",
        'FilbcC': "#" + presa_bcc + "#\n",
        'Fildis': "#" + input_dis + "#\n",
        'Flmap': "0 360 %i" % modeling_file.minutes_between_date(
            ini_date, end_date),
        'Zeta0': "0\n"
    }
    # Update params
    modeling_file.update_param_value(dic, f1, f2)

    f1.close()

    # f1 = open(base_path+'test_1.mdf', 'r')
    # f2 = open(base_path+'test_1_v2.mdf', 'w')
    os.rename(base_path + 'test_1.mdf', base_path + 'test_old.mdf')
    os.rename(base_path + 'test_1_v2.mdf', base_path + 'test_1.mdf')

    # WATER QUALITY
    ini_date_str = start_date.strftime('%Y/%m/%d') + '-00:00:00'
    end_date_str = end_date.strftime('%Y/%m/%d') + '-00:00:00'

    q1 = open(base_path + 'test_1.inp', 'r')
    q2 = open(base_path + 'test_1_v2.inp', 'w')

    # TODO
    wind_data = ini_date_str + '  2.55\n' + end_date_str + '  1.55\n'
    rad_data = ini_date_str + '  255.5\n' + end_date_str + '  155.5\n'

    # Layers
    # k = 35
    # Check Wind file
    print("Searching Wind data")
    print("Getting data")
    wind_block = False
    rad_block = False
    for line in q1:
        if wind_block is False and rad_block is False:
            if '2012.01.02 00:00:00' in line:
                line = line.replace(
                    '2012.01.02', "%s.%s.%s" % (
                        start_date.strftime('%Y'),
                        start_date.strftime('%m'),
                        start_date.strftime('%d')))
            if '2012/01/02-00:00:00' in line:
                line = line.replace('2012/01/02-00:00:00', ini_date_str)
            if '2012/01/05-00:00:00' in line:
                line = line.replace('2012/01/05-00:00:00', end_date_str)
            q2.write(line)
            if '; wind_start' in line:
                wind_block = True
                q2.write(wind_data)
            if '; rad_start' in line:
                wind_block = True
                q2.write(rad_data)
        elif wind_block:
            if '; wind_end' in line:
                q2.write(line)
                wind_block = False
        elif rad_block:
            if '; rad_end' in line:
                q2.write(line)
                rad_block = False

    q1.close()
    q2.close()

    os.rename(base_path + 'test_1.inp', base_path + 'test_old.inp')
    os.rename(base_path + 'test_1_v2.inp', base_path + 'test_1.inp')
    try:
        deployment_id = launch_orchestrator_job(
            'hydro', "%s/model_%s_%s/" % (
                region, start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')))
    except Exception as e:
        print(e)
        print("PaaS Orchestrator disconnected. Run the model manually")
        return "%s%s/model_%s_%s/" % (
            path, region, start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'))
    return deployment_id


def temp_map(file, ini_date, end_date, z):

    dataset_map = Dataset(file)
    sd = datetime.strptime(ini_date, '%Y-%m-%d %H:%M:%S')
    ed = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
    delta_time = (ed - sd).total_seconds()

    layer = int(((-z + 35) / 38) * 35)

    if (delta_time / 21600).is_integer:
        time = (delta_time / 21600)

        temp_map = dataset_map.variables["R1"][time][1][layer][:][:]
        temp_map = np.ma.masked_where(temp_map <= 0, temp_map)
        plt.figure(1, figsize=(20, 15))
        plt.imshow(np.flip(temp_map.transpose(), 0), aspect='auto')
        plt.colorbar()
        plt.xlabel('lon')
        plt.ylabel('lat')
        plt.title("Map Temp {}, prof = {} meters".format(end_date, z))
        plt.show()


def get_access_token(url):
    if url is None:
        url = 'https://iam.extreme-datacloud.eu/token'
    # TODO manage exceptions
    access_token = os.environ['OAUTH2_AUTHORIZE_TOKEN']
    refresh_token = os.environ['OAUTH2_REFRESH_TOKEN']

    IAM_CLIENT_ID = os.environ['IAM_CLIENT_ID']
    IAM_CLIENT_SECRET = os.environ['IAM_CLIENT_SECRET']

    data = {'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'client_id': IAM_CLIENT_ID,
            'client_secret': IAM_CLIENT_SECRET}
    print(data['client_id'])
    headers = {'Content-Type': 'application/json'}
    url = url + "?grant_type=refresh_token&refresh_token="
    url = url + refresh_token + '&client_id='
    url = url + IAM_CLIENT_ID + '&client_secret=' + IAM_CLIENT_SECRET

    r = requests.post(url, headers=headers)  # GET token
    print("Rquesting access token: %s" % r.status_code)
    # 200 means that the resource exists
    access_token = json.loads(r.content)['access_token']
    return access_token


def launch_orchestrator_job(model_type, model_path):

    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + access_token}

    tosca_file = ''
    if model_type == 'hydro':
        tosca_file = ".HY_MODEL.yml"

    with open(tosca_file, 'r') as myfile:
        tosca = myfile.read()

    data = {
        "parameters": {
            "cpus": 1,
            "mem": "4096 MB",
            "onedata_provider": "cloud-90-147-75-163.cloud.ba.infn.it",
            "model_space_name": "LifeWatch",
            "model_path": model_path,
            "output_filenames": "trim-test_1.nc",
            "onedata_zone": "https://onezone.cloud.cnaf.infn.it",
            "input_config_file": "config_d_hydro.xml"
            },
        "template": tosca
    }

    url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'
    r = requests.post(url, headers=headers, data=json.dumps(data))
    print("Status code: %s" % r.status_code)
    # 200 means that the resource exists
    print(r.headers)
    txt = json.loads(r.text)
    print(json.dumps(txt, indent=2, sort_keys=True))
    # print(r.text)
    # print(r.reason)
    deployment_id = json.loads(r.content)['uuid']
    print("Deployment ID: %s" % deployment_id)
    return deployment_id


def launch_orchestrator_sat_job(start_date, end_date,
                                region, sat_type, sat_path):

    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + access_token}

    tosca_file = '.SAT_DATA.yml'

    with open(tosca_file, 'r') as myfile:
        tosca = myfile.read()

    data = {
        "parameters": {
            "cpus": 1,
            "mem": "4096 MB",
            "onedata_provider": "cloud-90-147-75-163.cloud.ba.infn.it",
            "sat_space_name": "LifeWatch",
            "sat": sat_type,
            "sat_path": sat_path,
            "region": region,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "onedata_zone": "https://onezone.cloud.cnaf.infn.it"
        },
        "template": tosca
    }

    url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'
    r = requests.post(
        url, headers=headers,
        data=json.dumps(data))  # GET
    print("Status code SAT: %s" % r.status_code)
    # 200 means that the resource exists
    print(r.headers)
    txt = json.loads(r.text)
    print(json.dumps(txt, indent=2, sort_keys=True))
    # print(r.text)
    # print(r.reason)
    deployment_id = json.loads(r.content)['uuid']
    print("Deployment ID: %s" % deployment_id)
    return deployment_id


def orchestrator_job_status(deployment_id):
    # TODO manage exceptions
    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'
    url = url + deployment_id
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + access_token}
    r = requests.get(url, headers=headers)  # GET token
    print("Status code: %s" % r.status_code)
    txt = json.loads(r.text)
    print(json.dumps(txt, indent=2, sort_keys=True))
    # print(r.text)
    # print(r.reason)
    return r.content


def orchestrator_list_deployments(orchestrator_url):
    # TODO manage exceptions
    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    if orchestrator_url is None:
        orchestrator_url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/'

    url = orchestrator_url + "deployments?createdBy="
    url = url + os.environ['JUPYTERHUB_USER']
    url = url + "@https://iam.extreme-datacloud.eu/"
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + access_token}
    r = requests.get(url, headers=headers)  # GET
    return json.loads(r.content)['content']


def menu():
    # ################### MENU ##################################
    onedata_wid = widgets.Text(
        value='',
        placeholder='Onedata token',
        description='Onedata token:',
        disabled=False
    )
    onedata_wid.value = os.environ['ONECLIENT_AUTHORIZATION_TOKEN']

    region_buttons = widgets.ToggleButtons(
        options=['CdP', 'Sanabria'],
        description='Reservoirs/Lakes:',
    )
    ini_date = widgets.DatePicker(
        description='Initial Date',
        disabled=False
    )
    end_date = widgets.DatePicker(
        description='End Date',
        disabled=False
    )
    actions = widgets.SelectMultiple(
        options=['meteo', 'water_mask', 'water_surface',
                 'cloud_mask', 'cloud_coverage',
                 'list_files', 'download_sat_data',
                 'model'],
        value=['meteo'],
        # rows=10,
        description='Actions',
        disabled=False
    )
    tab = VBox(
        children=[
            onedata_wid, region_buttons,
            ini_date, end_date, actions])

    button = widgets.Button(
        description='Run',
    )

    # last_model = ''

    out = widgets.Output()
    @button.on_click
    def plot_on_click(b):
        with out:
            clear_output()
            if actions.value[0] == 'meteo':
                plot_meteo(region_buttons, ini_date, end_date, actions)
            elif actions.value[0] == 'list_files':
                find_dataset_type(
                    ini_date.value, end_date.value,
                    '', onedata_wid.value)
            elif actions.value[0] == 'download_sat_data':
                launch_orchestrator_sat_job(
                    ini_date.value, end_date.value,
                    region_buttons.value,
                    'Landsat8', '/xdc_lfw_sat/datesets/')
            elif actions.value[0] == 'model':
                # last_model =
                prepare_model(
                    ini_date.value, end_date.value,
                    region_buttons.value,
                    '/home/jovyan/datasets/LifeWatch/', onedata_wid.value)
            else:
                plot_satellite(region_buttons, ini_date, end_date, actions)

    vbox1 = VBox(children=[tab, button, out])
    # Jobs
    job_list = []
    for e in orchestrator_list_deployments(None):
        job_list.append(
            'ID: %s | Creation time: %s | Status: %s' % (
                e['uuid'], e['creationTime'], e['status']))

    selection_jobs = widgets.Select(
        options=job_list,
        value=None,
        # rows=10,
        description='Job List',
        disabled=False,
        layout=Layout(width='90%')
    )

    button2 = widgets.Button(
        description='Show deployment',
    )

    out2 = widgets.Output()

    @button2.on_click
    def model_on_click(b):
        with out2:
            clear_output()
            jb = selection_jobs.value
            orchestrator_job_status(
                jb[jb.find('ID: ', 0) + len('ID: '):jb.find(' | ')])

    vbox2 = VBox(children=[selection_jobs, button2, out2])

    # Model visualization
    onedata_token = os.environ['ONECLIENT_AUTHORIZATION_TOKEN']
    models = find_models(onedata_token)
    opt = []
    for e in models:
        opt.append("%s%s%s%s%s%s" % (e['key']['region'], '/model_', e['key']['beginDate'], '_', e['key']['endDate'], '/trim-test_1.nc'))
        opt.append("%s%s%s%s%s%s" % (e['key']['region'], '/model_', e['key']['beginDate'], '_', e['key']['endDate'], '/test_1_map.nc'))
    if len(opt) == 0:
        opt.append('No models')

    box_layout = Layout(display='flex',
                        align_items='center',
                        width='auto',
                        justify_content='space-around')

    # Inicializacion de widgets del menu
    selection = widgets.Select(
        options=opt,
        value=opt[0],
        # rows=10,
        description='Models',
        disabled=False,
        layout=Layout(width='75%')
    )

    depth_wid = widgets.IntSlider(
        value=7,
        min=0,
        max=34,
        step=1,
        description='Layer (depth):',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='d'
    )
    button_model_output = widgets.Button(
        description='Show model output',
    )

    ruta = '/home/jovyan/datasets/LifeWatch/'

    out3 = widgets.Output()

    # Cuando se clica el boton se carga el fichero
    # con el modulo indicado y se muestra la info

    @button_model_output.on_click
    def model_on_click(b):
        global dataset, variables, propiedades, range_index, animacion_on
        animacion_on = False
        nombre_dataset = ruta + "/" + selection.value
        dataset = Dataset(nombre_dataset, 'r', format='NETCDF4_CLASSIC')
        # variables[nombre_variable, num_dim, descripcion]
        variables = [[], [], []]
        # propiedades[index_var_escogida, fecha,profundidad,
        # min_v/alue_var, max_value_var, mean_value_var]
        propiedades = [[], [], [], [], [], []]

        carga_variables()
        propiedades[0] = 0
        range_index = 1
        set_widgets()

        with out3:
            propiedades[1] = drop_date.value
            propiedades[2] = depth_wid.value
            calcula_min_max()
            actualiza_layout()

    # Se comprueba cual es la variable tiempo en el
    # modelo y se cargan en "variables" las variables del modelo

    def carga_variables():
        global drop_var, variables, time, tipo
        # tipo 0 = calidad del agua, prof de mas profundo a menos
        # tipo 1 = hidrodinamico?, prof de menos a mas
        tipo = 1
        for n in dataset.variables.keys():
            if n.find("R1") >= 0 and tipo == 1:
                tipo = 0
                variables[0] = np.append(variables[0], "TEMPERATURE")
                variables[1] = np.append(variables[1], -1)
                variables[2] = np.append(variables[2], "TEMPERATURE")
            if n.find("time") >= 0:
                time = n
            dimensiones = ''
            for i in dataset.variables[n].dimensions:
                dimensiones = dimensiones + " " + i

            dim = len(dataset.variables[n].dimensions)
            if dim > 2 and dim < 5:
                variables[0] = np.append(variables[0], n)
                variables[1] = np.append(variables[1], dim)
                try:
                    des = (n + ": " + dataset.variables[n].long_name)
                except Exception:
                    des = (n)
                variables[2] = np.append(variables[2], des)
        if 'nmesh2d_dlwq_time' in dataset.variables.keys():
            time = 'nmesh2d_dlwq_time'
            tipo = 0

    # Se inicializan los widgets

    def set_widgets():
        global drop_var, drop_date, depth_wid, hb_3d, hb_2d
        global vb_ev_2d, vb_ev_3d, valor_x, valor_y, date
        global drop_date_range2, drop_date_range1

        # widgets para escoger que datos mostrar
        drop_var = widgets.Dropdown(
            options=[(variables[2][n], n) for n in range(len(variables[2]))],
            value=0,
            description='Variables:',
        )
        date = set_date()
        drop_date = widgets.Dropdown(
            options=[(str(date[i]), i) for i in range(len(date))],
            value=0,
            description='Date:',
        )
        depth_wid = widgets.IntSlider(
        value=7,
        min=0,
        max=34,
        step=1,
        description='Layer (depth):',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='d'
        )
        button_model_output = widgets.Button(
            description='Show model output',
        )
    
        drop_date.observe(date_on_change, names='value')
        drop_var.observe(variable_on_change, names='value')
        hb_3d = HBox([drop_var, drop_date, depth_wid])
        hb_2d = HBox([drop_var, drop_date])

        # cuadro de texto para donde se escoge el valor de coordenada x e y
        valor_x = widgets.BoundedFloatText(
            value=0, min=0,
            max=dataset.variables[variables[0][propiedades[0]]].shape[-2] - 1,
            step=1, description='x:')
        valor_y = widgets.BoundedFloatText(
            value=0, min=0,
            max=dataset.variables[variables[0][propiedades[0]]].shape[-1] - 1,
            step=1, description='y:')

        # widgets para ver mas info
        boton_tiempo = widgets.Button(
            description='Tiempo'
        )

        boton_animacion = widgets.Button(
            description='Animacion evolucion'
        )

        boton_prof = widgets.Button(
            description='Profundidad'
        )

        boton_corte_lon = widgets.Button(
            description='Longitudinal'
        )

        boton_corte_lat = widgets.Button(
            description='Latitudinal'
        )

        Label_cor = widgets.Label(
            "Clicar en el mapa para escoger coordenadas:")
        Label_display = widgets.Label("Mostrar:")
        Label_date = widgets.Label("Rango de fechas:")
        Label_section = widgets.Label("Mapa con corte:")
        Label_plot = widgets.Label("Diagrama con evolucion en funcion:")

        drop_date_range1 = widgets.Dropdown(
            options=[
                (str(date[i]), i)
                for i in range(0, len(date) - range_index)],
            value=0,
            description='Desde:',
        )

        drop_date_range2 = widgets.Dropdown(
            options=[(str(date[i]), i) for i in range(range_index, len(date))],
            value=len(date) - range_index,
            description='Hasta:',
        )

        vb_cor = VBox([Label_cor, valor_x, valor_y])
        vb_date_range = VBox([Label_date, drop_date_range1, drop_date_range2])
        hb_options = HBox([vb_cor, vb_date_range])

        hb_corte = HBox([boton_corte_lat, boton_corte_lon], layout=box_layout)
        hb_plot = HBox([boton_tiempo, boton_prof], layout=box_layout)
        hb_time = HBox([boton_tiempo], layout=box_layout)

        vb_ev_3d = VBox(
            [hb_options,
             Label_display,
             boton_animacion,
             Label_section,
             hb_corte,
             Label_plot, hb_plot])
        vb_ev_2d = VBox(
            [hb_options, Label_display,
             boton_animacion, Label_plot,
             hb_time])

        widgets.interact(
            drop_date_range1=drop_date_range1,
            drop_date_range2=drop_date_range2)
        drop_date_range1.observe(range_on_change, names='value')
        boton_prof.on_click(on_button_clicked_ev_prof)
        boton_tiempo.on_click(on_button_clicked_ev_time)
        boton_animacion.on_click(on_button_clicked_animacion)
        boton_corte_lat.on_click(on_button_clicked_corte_lat)
        boton_corte_lon.on_click(on_button_clicked_corte_lon)

    # Se convierte de segundos a fechas

    def set_date():
        date = []
        t = dataset.variables[time].units
        year = int(re.findall(r'seconds since ([0-9]*)-', t)[0])
        month = int(re.findall(r'seconds since [0-9]*-([0-9]*)', t)[0])
        day = int(re.findall(r'seconds since [0-9]*-[0-9]*-([0-9]*)', t)[0])

        a = datetime(year, month, day, 0, 0, 0)

        for n in dataset.variables[time]:
            b = a + timedelta(seconds=int(n))
            date = np.append(date, b)

        return date

    # Se actualiza la interfaz para mostrar
    # los nuevos datos despues de un cambio

    def actualiza_layout():
        if animacion_on:
            anim.event_source.stop()
        clear()
        # Mostrar estadisticas de las variables
        max_value = "Max value: " + str(propiedades[4])
        min_value = "Min value: " + str(propiedades[3])
        mean_value = "Mean value: " + str(propiedades[5])

        # Muestra, si la hay, la descripcion de las variables
        des = ""
        try:
            des = (
                variables[0][propiedades[0]] +
                + ": " +
                + dataset.variables[
                    variables[0][propiedades[0]]].long_name)
        except Exception:
            des = ("Variable sin descripcion")
        label = widgets.Label(des)
        label_min = widgets.Label(min_value)
        label_max = widgets.Label(max_value)
        label_mean = widgets.Label(mean_value)
        hb_max_min = HBox([label_min, label_max, label_mean])

        hb_range = HBox([min_range, max_range, boton_range])

        # Comprueba de que depende las variables
        # y escoge que pasarle dependiendo de eso
        if variables[1][propiedades[0]] == 4:
            depth_wid.max = dataset.variables[
                variables[0][propiedades[0]]].shape[-3] - 1
            display(hb_3d, label, hb_max_min, hb_range)
            prof = propiedades[2]
            if tipo == 0:
                dimz = dataset.variables[
                    variables[0][propiedades[0]]].shape[-3] - 1
                prof = dimz - prof
            aux = dataset.variables[variables[0][propiedades[0]]][
                propiedades[1], prof, :, :]
            ev = vb_ev_3d

        if variables[1][propiedades[0]] == - 1:
            depth_wid.max = dataset.variables["R1"].shape[-3] - 1
            display(hb_3d, label, hb_max_min, hb_range)
            prof = propiedades[2]
            dimz = dataset.variables["R1"].shape[-3] - 1
            prof = dimz - prof
            aux = dataset.variables["R1"][propiedades[1], 1, prof, :, :]
            ev = vb_ev_3d

        if variables[1][propiedades[0]] == 3:
            display(hb_2d, label, hb_max_min, hb_range)
            aux = dataset.variables[
                variables[0][propiedades[0]]][propiedades[1], :, :]
            ev = vb_ev_2d

        aux = np.transpose(aux)

        # Convierte los valores de relleno en nan
        # para que no se pinten en el mapa
        v_m = np.nanmin(aux[:])
        try:
            aux[aux == v_m] = np.nan
        except Exception:
            print("fallo")

        fig = imshow_rango(aux, min_range.value, max_range.value)

        # Se crea un evento para coger las coordenadas escogidas
        # cid =
        fig.canvas.mpl_connect('button_press_event', onclick)

        display(ev)

    # pintar el plt.imshow con rango de valores

    def imshow_rango(v1, imin, imax):

        # Se crea un maskarray que contenga los valores
        # dentro del rango y otro que no, para pintarlos
        # con rangos de colores distintos
        v1b = masked_inside(v1, imin, imax)
        v1a = masked_outside(v1, imin, imax)

        fig, ax = plt.subplots()
        fig.tight_layout
        pa = ax.imshow(
            v1a, interpolation='nearest',
            cmap=matplotlib.cm.jet,
            vmin=min_range.value, vmax=max_range.value)
        # pb =
        ax.imshow(
            v1b, interpolation='nearest',
            cmap=matplotlib.cm.Pastel1, vmax=3, vmin=3)
        cbar = plt.colorbar(pa, shrink=0.25)

        try:
            cbar.set_label(
                dataset.variables[variables[0][propiedades[0]]].units)
        except Exception:
            cbar.set_label("Unidades no especificadas")
        plt.title(variables[0][propiedades[0]])
        plt.ylabel("Latitude")
        plt.xlabel("Longitude")

        plt.show()

        return fig

    # Cuando se clica en el mapa se guardan los valores de las cordenadas

    def onclick(event):
        global valor_x, valor_y
        valor_x.value = int(event.xdata)
        valor_y.value = int(event.ydata)

    # Se vacia el output y se cierran las figuras plt

    def clear():
        clear_output()
        plt.close()

    # Cuando se cambia la variable escogidase
    # calcula las estadisticas de la variable
    # y se actualiza lo que se muestra por pantalla

    def variable_on_change(v):
        propiedades[0] = v['new']
        propiedades[3] = None
        propiedades[4] = None
        calcula_min_max()
        actualiza_layout()

    # Calcula las estadisticas de la variable (min, max, mean)

    def calcula_min_max():
        global min_range, max_range, boton_range

        if variables[1][propiedades[0]] == -1:
            var = dataset.variables["R1"][:, 1, :, :, :]
        else:
            var = dataset.variables[variables[0][propiedades[0]]][:]
        v_m = np.nanmin(var[:])
        try:
            var[var == v_m] = np.nan
        except Exception:
            print("fallo")

        v_mean = np.nanmean(var[:])
        v_max = np.nanmax(var[:])
        v_min = np.nanmin(var[:])

        propiedades[3] = v_min
        propiedades[4] = v_max
        propiedades[5] = v_mean

        # Casillas para escoger e rango de valores que se quieren mostrar
        min_range = widgets.BoundedFloatText(
            value=propiedades[3],
            min=propiedades[3],
            max=propiedades[4],
            step=1,
            description='Min:')

        max_range = widgets.BoundedFloatText(
            value=propiedades[4],
            min=propiedades[3],
            max=propiedades[4],
            step=1,
            description='Max:')

        boton_range = widgets.Button(
            description='Change range'
        )
        boton_range.on_click(on_button_clicked_range)

    # Se actualiza la profundidad y se actualiza la interfaz

    def slider_on_change(v):

        propiedades[2] = v['new']
        actualiza_layout()

    depth_wid.observe(slider_on_change, names='value')

    # Se cambia la fecha a observar y se muestran los datos acorde a esa fecha

    def date_on_change(v):
        propiedades[1] = v['new']
        actualiza_layout()

    def range_on_change(v):
        range_index = v['new']
        v = drop_date_range2.value
        if range_index > v:
            v = range_index
        drop_date_range2.options = [
            (str(date[i]), i)
            for i in range(range_index + 1, len(date))]
        drop_date_range2.value = v

    # Se muestra la ev en profundidad

    def muestra_ev_prof():

        fig3 = plt.figure()
        fig3.add_subplot()

        if variables[1][propiedades[0]] == -1:
            dimz = dataset.variables["R1"].shape[-3]
            eje_x = [dataset.variables["R1"][
                propiedades[1], 1,
                i, valor_x.value,
                valor_y.value] for i in range(dimz)]
        else:
            dimz = dataset.variables[variables[0][propiedades[0]]].shape[-3]
            eje_x = [dataset.variables[variables[0][propiedades[0]]][
                propiedades[1],
                i, valor_x.value,
                valor_y.value] for i in range(dimz)]

        eje_y = [i for i in range(dimz)]
        plt.gca().invert_yaxis()

        plt.plot(eje_x, eje_y)

        plt.title(variables[0][propiedades[0]])
        plt.ylabel("layer")

        try:
            plt.xlabel(
                variables[0][propiedades[0]] +
                + ": " +
                + dataset.variables[variables[0][propiedades[0]]].units)
        except Exception:
            plt.xlabel("#")

    # Se muestra la evolucion en funcion del tiempo
    def muestra_ev_tiempo():
        fig3 = plt.figure()
        fig3.add_subplot()

        drop_date_range2.value

        eje_x = [
            date[i]
            for i in range(drop_date_range1.value, drop_date_range2.value)]
        ax = []
        for i in range(
            drop_date_range1.value, int(drop_date_range2.value / 4)):
            monthinteger = date[4 * i].month
            month = datetime(2000, monthinteger, 1).strftime('%B')
            d = str(month) + "-" + str(date[i * 4].day)
            ax = np.append(ax, d)
            ax = np.append(ax, " ")
            ax = np.append(ax, " ")
            ax = np.append(ax, " ")

        if variables[1][propiedades[0]] == 4:
            eje_y = [dataset.variables[variables[0][propiedades[0]]][
                i, propiedades[2], valor_x.value, valor_y.value]
                for i in range(drop_date_range1.value, drop_date_range2.value)]

        if variables[1][propiedades[0]] == 3:
            eje_y = [dataset.variables[variables[0][propiedades[0]]][
                i, valor_x.value, valor_y.value]
                for i in range(drop_date_range1.value, drop_date_range2.value)]

        if variables[1][propiedades[0]] == -1:
            eje_y = [dataset.variables["R1"][
                i, 1, propiedades[2],
                valor_x.value, valor_y.value]
                for i in range(drop_date_range1.value, drop_date_range2.value)]

        plt.xticks(eje_x, ax)
        plt.plot(eje_x, eje_y)
        plt.title(variables[0][propiedades[0]])
        plt.xlabel("date")

        try:
            plt.ylabel(
                variables[0][propiedades[0]] +
                + ": " +
                + dataset.variables[variables[0][propiedades[0]]].units)
        except Exception:
            plt.ylabel("#")

    # Metodos de botones

    def on_button_clicked_ev_prof(b):
        actualiza_layout()
        muestra_ev_prof()

    def on_button_clicked_ev_time(b):
        actualiza_layout()
        muestra_ev_tiempo()

    def on_button_clicked_range(b):
        actualiza_layout()

    def on_button_clicked_animacion(b):
        global anim
        # animacion_on = True
        actualiza_layout()
        anim = animacion()

    # Muestra el corte en latitud de unas cordenadas escogidas
    def on_button_clicked_corte_lat(b):
        actualiza_layout()
        if variables[1][propiedades[0]] == -1:
            dimz = dataset.variables["R1"].shape[-3]
            dimx = dataset.variables["R1"].shape[-2]
        else:
            dimz = dataset.variables[variables[0][propiedades[0]]].shape[-3]
            dimx = dataset.variables[variables[0][propiedades[0]]].shape[-2]
        corte_latitud(valor_y.value, dimx,
                      dimz, min_range.value,
                      max_range.value)

    # Muestra el corte longitudinal de unas cordenadas escogidas

    def on_button_clicked_corte_lon(b):
        actualiza_layout()
        if variables[1][propiedades[0]] == -1:
            dimz = dataset.variables["R1"].shape[-3]
            dimy = dataset.variables["R1"].shape[-1]
        else:
            dimz = dataset.variables[
                variables[0][propiedades[0]]].shape[-3]
            dimy = dataset.variables[
                variables[0][propiedades[0]]].shape[-1]

        corte_longitud(valor_x.value,
                       dimy, dimz, min_range.value,
                       max_range.value)

    # Crea el corte longitudinal

    def corte_longitud(lon, dim, dimz, imin, imax):
        corte = np.zeros((dimz, dim))
        step = 1
        z0 = 0
        z1 = dimz - 1
        if tipo == 0:
            z0 = dimz - 1
            z1 = 0
            step = -1

        if variables[1][propiedades[0]] == -1:
            for i in range(z0, z1, step):
                aux = dataset.variables["R1"][propiedades[1], 1, i, lon, :]
                corte[i, :] = aux
        else:
            for i in range(z0, z1, step):
                aux = dataset.variables[
                    variables[0][
                        propiedades[0]]][propiedades[1], i, lon, :]
                corte[i, :] = aux

        v_m = np.nanmin(corte[:])
        try:
            corte[corte == v_m] = np.nan
        except Exception:
            print("fallo")

        v1b = masked_inside(corte, imin, imax)
        v1a = masked_outside(corte, imin, imax)

        fig, ax = plt.subplots()
        fig.tight_layout
        pa = ax.imshow(
            v1a, interpolation='nearest',
            cmap=matplotlib.cm.jet, vmin=min_range.value,
            vmax=max_range.value)
        # pb =
        ax.imshow(
            v1b, interpolation='nearest',
            cmap=matplotlib.cm.Pastel1, vmax=3, vmin=3)
        # cbar =
        plt.colorbar(pa, shrink=0.25)

    # Crea el corte en latitud
    def corte_latitud(lat, dim, dimz, imin, imax):
        corte = np.zeros((dimz, dim))
        step = 1
        z0 = 0
        z1 = dimz - 1
        if tipo == 0:
            z0 = dimz - 1
            z1 = 0
            step = -1

        if variables[1][propiedades[0]] == - 1:
            for i in range(z0, z1, step):
                aux = dataset.variables["R1"][propiedades[1], 1, i, :, lat]
                corte[i, :] = aux
        else:
            for i in range(z0, z1, step):
                aux = dataset.variables[
                    variables[0][
                        propiedades[0]]][propiedades[1], i, :, lat]
                corte[i, :] = aux

        v_m = np.nanmin(corte[:])
        try:
            corte[corte == v_m] = np.nan
        except Exception:
            print("fallo")

        v1b = masked_inside(corte, imin, imax)
        v1a = masked_outside(corte, imin, imax)

        fig, ax = plt.subplots()
        fig.tight_layout
        pa = ax.imshow(v1a, interpolation='nearest',
                       cmap=matplotlib.cm.jet, vmin=min_range.value,
                       vmax=max_range.value)
        # pb =
        ax.imshow(v1b, interpolation='nearest',
                  cmap=matplotlib.cm.Pastel1,
                  vmax=3, vmin=3)
        # cbar =
        plt.colorbar(pa, shrink=0.25)

    # Crea una animacion sobre la evolucion de la variable en una cierta
    # profundidad en el tiempo y retorna una instancia de ella para que
    # se ejecute correctamente
    def animacion():
        global snapshots, im, fig

        if variables[1][propiedades[0]] == 4:
            prof = propiedades[2]
            if tipo == 0:
                dimz = dataset.variables[
                    variables[0][propiedades[0]]].shape[-3] - 1
                prof = dimz - prof
            snapshots = [np.transpose(
                dataset.variables[variables[0][propiedades[0]]][i, prof, :, :])
                for i in range(drop_date_range1.value, drop_date_range2.value)]
            # ev = vb_ev_3d

        if variables[1][propiedades[0]] == 3:
            snapshots = [np.transpose(
                dataset.variables[variables[0][propiedades[0]]][i, :, :])
                for i in range(drop_date_range1.value, drop_date_range2.value)]

        if variables[1][propiedades[0]] == -1:
            prof = propiedades[2]
            dimz = dataset.variables["R1"].shape[-3] - 1
            prof = dimz - prof
            snapshots = [
                np.transpose(
                    dataset.variables["R1"][i, 1, prof, :, :]) for i in range(
                        drop_date_range1.value, drop_date_range2.value)]
            # ev = vb_ev_3d

        v_m = np.nanmin(snapshots[0][:])
        for i in range(len(snapshots)):
            aux = snapshots[i]
            try:
                aux[aux == v_m] = np.nan
            except Exception:
                print("fallo")
            snapshots[i] = aux

        fig = plt.figure()

        a = snapshots[0]

        plt.tight_layout
        im = plt.imshow(a, interpolation='none', aspect='auto',
                        cmap=matplotlib.cm.jet, vmin=propiedades[3],
                        vmax=propiedades[4])
        plt.colorbar()

        anim = animation.FuncAnimation(
            fig,
            animate_func,
            frames=len(date),
            interval=500,  # in ms
            )
        return anim

    # Funcion para crear la animacion
    def animate_func(i):
        im.set_array(snapshots[i])
        plt.title(date[i])
        return [im]

    vbox3 = VBox(children=[selection, button_model_output, out3])

    # Menu
    menu = widgets.Tab()
    menu.children = [vbox1, vbox2, vbox3]
    menu.set_title(0, 'Data Ingestion')
    menu.set_title(1, 'Job status')
    menu.set_title(2, 'Model visualization')
    return menu
