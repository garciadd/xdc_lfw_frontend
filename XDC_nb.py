#import APIs
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from datetime import datetime
from dateutil import parser
import numpy as np
import os, shutil
import requests
import json
from netCDF4 import Dataset

#import satellite submodules
from wq_modules import sentinel
from wq_modules import landsat
from wq_modules import water
from wq_modules import clouds
from wq_modules import modeling_file

#import meteo submodules
from wq_modules import meteo

#import general submodules
from wq_modules import utils
from wq_modules import config

#widget
import ipywidgets as widgets
from ipywidgets import HBox, VBox, Layout
from IPython.display import display
from IPython.display import clear_output

def plot_meteo(region_buttons, ini_date, end_date, actions):
    region = region_buttons.value
    sd = ini_date.value
    #datetime.strptime(ini_date.value, "%m-%d-%Y")
    ed = end_date.value
    m = meteo.Meteo(sd, ed, region)
    m.params = ["ID","Date","Temp"]
    meteo_output = m.get_meteo()
    data = pd.read_csv(meteo_output['output'],delimiter=';',decimal=',')
    data['Date'] = pd.to_datetime(data['Date'])
    #data["Temp"] = float(data["Temp"])
    data
    data.plot(x='Date', y='Temp')
    plt.show()



def plot_satellite(region_buttons, ini_date, end_date, actions):

    #Check the format date and if end_date > start_date
    st_date = ini_date.value
    ed_date = end_date.value
    sd, ed = utils.valid_date(st_date, ed_date)

    #chek the region to attach coordinates
    region = region_buttons.value
    utils.valid_region(region)

    #check if the action exist in the Keywords list of config file
    act = actions.value[0]
    utils.valid_action(act)

    #Configure the tree of the temporal datasets path. Create the folder and the downloaded_files file
    onedata_mode = config.onedata_mode
    utils.path_configurations(onedata_mode)

    #Action management
    if act is not None:

        #download sentinel files
        s = sentinel.Sentinel(sd, ed, region, act)
        s.download()
        sentinel_files = s.__dict__['output']

        #download landsat files
        l = landsat.Landsat(sd, ed, region, act)
        l.download()
        landsat_files = l.__dict__['output']

        if onedata_mode == 1:
            utils.clean_temporal_path()

        if act == 'water_mask' or act == 'water_surface':

            water.main_water(sentinel_files, landsat_files, region, act)

        elif act == 'cloud_mask' or act == 'cloud_coverage':

            clouds.main_cloud(sentinel_files, landsat_files, region, act)

def find_dataset_type(start_date,end_date,typ,onedata_token):
    headers = {"X-Auth-Token": onedata_token}
    url = 'https://cloud-90-147-75-163.cloud.ba.infn.it/api/v3/oneprovider/spaces/17d670040b30511bc4848cab56449088'
    r = requests.get(url, headers=headers)
    space_id = json.loads(r.content)['spaceId']
    print('Onedata space ID: %s' % space_id)
    index_name = 'region_type__query'
    onedata_cdmi_api = 'https://cloud-90-147-75-163.cloud.ba.infn.it/cdmi/cdmi_objectid/'
    url = 'https://cloud-90-147-75-163.cloud.ba.infn.it/api/v3/oneprovider/spaces/'+space_id+'/indexes/'+index_name+'/query'
    r = requests.get(url, headers=headers)
    response = json.loads(r.content)
    result = []
    for e in response:
        if typ in e['key']['dataset']:
            print(e['key']['dataset'])
            if check_date(start_date,end_date,e['key']['beginDate'], e['key']['endDate']):
                print({'beginDate': e['key']['beginDate'], 'endDate': e['key']['endDate'], 'file':e['key']['dataset']})
                result.append({'beginDate': e['key']['beginDate'], 'endDate': e['key']['endDate'], 'file':e['key']['dataset']})
    return result

def find_models(onedata_token):
    headers = {"X-Auth-Token": onedata_token}
    url = 'https://cloud-90-147-75-163.cloud.ba.infn.it/api/v3/oneprovider/spaces/17d670040b30511bc4848cab56449088'
    r = requests.get(url, headers=headers)
    space_id = json.loads(r.content)['spaceId']
    print('Searching models')
    index_name = 'models_region_query'
    onedata_cdmi_api = 'https://cloud-90-147-75-163.cloud.ba.infn.it/cdmi/cdmi_objectid/'
    url = 'https://cloud-90-147-75-163.cloud.ba.infn.it/api/v3/oneprovider/spaces/'+space_id+'/indexes/'+index_name+'/query'
    r = requests.get(url, headers=headers)
    response = json.loads(r.content)
    #headers = {'X-Auth-Token': onedata_token, 'X-CDMI-Specification-Version': '1.1.1'}
    #result = []
    #for e in response:
        #print(e['id'])
        #print('-------------')
     #   res = requests.get(onedata_cdmi_api+e['value'],headers=headers)
     #   element = json.loads(res.content)
    
     #   try:
      #      result.append({'model_output': element['metadata']['onedata_json']['eml:eml']['dataset']['title'], 'beginDate': element['metadata']['onedata_json']['eml:eml']['dataset']['coverage']['temporalCoverage']['rangeOfDates']['beginDate']['calendarDate'], 'endDate': element['metadata']['onedata_json']['eml:eml']['dataset']['coverage']['temporalCoverage']['rangeOfDates']['endDate']['calendarDate']})
      #  except:
      #      pass
    
    return response

def check_date(start_date, end_date, meta_beginDate, meta_endDate):
    meta_start_date = parser.parse(meta_beginDate)
    meta_end_date = parser.parse(meta_endDate)
    try:
        print("Selected [start: %s end: %s ] | Metadata: [start: %s end: %s]" % (start_date,end_date, meta_start_date, meta_end_date))
        if meta_start_date.date() <= start_date and meta_end_date.date() >= end_date:
            print("Candidate File")
            return True
        elif meta_start_date.date() == meta_end_date.date() and meta_start_date.date() >= start_date and meta_end_date.date() <= end_date:
            print("Candidate File")
            return True
        else:
            return False
    except ValueError:
        print("Wrong Date format")
        return False
   
   
def prepare_model(start_date, end_date, region, path,onedata_token):
     #Parameters
    ini_date_str = start_date.strftime('%Y-%m-%d')+' 00:00:00'
    end_date_str = end_date.strftime('%Y-%m-%d')+' 00:00:00'
    
    print("Generating new model"+'/model_'+start_date.strftime('%Y-%m-%d')+'_'+end_date.strftime('%Y-%m-%d')+'/')
    try:
        shutil.copytree(path+region+'/model', path+region+'/model_'+start_date.strftime('%Y-%m-%d')+'_'+end_date.strftime('%Y-%m-%d')+'/')
        
    except FileExistsError:
        shutil.rmtree(path+region+'/model_'+start_date.strftime('%Y-%m-%d')+'_'+end_date.strftime('%Y-%m-%d')+'/')
        shutil.copytree(path+region+'/model', path+region+'/model_'+start_date.strftime('%Y-%m-%d')+'_'+end_date.strftime('%Y-%m-%d')+'/')
    base_path = path+region+'/model_'+start_date.strftime('%Y-%m-%d')+'_'+end_date.strftime('%Y-%m-%d')+'/'
    fmt = '%Y-%m-%d %H:%M:%S'
    ini_date = datetime.strptime(ini_date_str, fmt)
    end_date = datetime.strptime(end_date_str, fmt)    
    

    f1 = open(base_path+'test_1.mdf','r')
    f2 = open(base_path+'test_1_v2.mdf','w')

    #Layers
    k = 35
    print(modeling_file.minutes_between_date(ini_date,end_date))

    #Check Wind file
    
    wind_input = ''
    #Search once. If it is not found, it tries to download the data
    try:
        print("Searching Wind data")
        wind_input = '/home/jovyan/datasets/LifeWatch/'+region+'/'+find_dataset_type(ini_date.date(),end_date.date(),'wind',onedata_token)[0]["file"]
    except Exception as e:
        print(e)
        print("Getting data")
        m = meteo.Meteo(ini_date.date(), end_date.date(), region)
        m.params = ["ID","date","speed","dir"]
        wind_input = m.get_meteo()['output']
    #Second time. If it is not found, it generates a generic file.
    try:
        if wind_input == '':
            print("Searching Wind data again")
            wind_input = '/home/jovyan/datasets/LifeWatch/'+ region + '/' + find_dataset_type(ini_date.date(),end_date.date(),'wind',onedata_token)[0]["file"]
    except:
        wf = open(base_path+'wind_generic.csv','w')
        line = "date;speed;dir\n\"%s\";2.72;277\n\"%s\";2.72;277\n" % (ini_date_str, end_date_str)
        wf.write(line)
        wf.close()
        wind_input = base_path+'wind_generic.csv'
        
    print("Creating file .wnd from CSV: %s" % wind_input)
    wind_file_name = "wind_"+ini_date.strftime('%Y-%m-%d%H%M%S')+"_"+end_date.strftime('%Y-%m-%d%H%M%S')+".wnd"
    modeling_file.csv_to_wind(wind_input, ini_date, end_date, base_path+wind_file_name)
    print("Wind file created: %s" % wind_file_name)


    #Check initial conditions
    #TODO For the moment, only with uniform values
    print("Searching Initial data")
    print("Getting initial data")
    print("Creating initial data file .ini")
    ini_file_name = "initial_"+ini_date.strftime('%Y-%m-%d%H%M%S')+"_"+end_date.strftime('%Y-%m-%d%H%M%S')+".ini"
    print("Initial file created: %s" % ini_file_name)

    #Check Radiation file
    print("Searching Radiation data")
    print("Getting data")
    try:
        rad_input = '/home/jovyan/datasets'+find_dataset_type(ini_date.date(),end_date.date(),'rad')[0]['file']
    except:
        rf = open(base_path+'rad_generic.csv','w')
        line = "date;hum;temp;rad\n\"%s\";22.72;12.4;0\n\"%s\";22.72;12.4;200\n" % (ini_date_str, end_date_str)
        rf.write(line)
        rf.close()
        rad_input = base_path+'rad_generic.csv'
    print("Creating file .tem")
    rad_file_name = "rad_"+ini_date.strftime('%Y-%m-%d%H%M%S')+"_"+end_date.strftime('%Y-%m-%d%H%M%S')+".tem"
    modeling_file.csv_to_tem(rad_input, ini_date, end_date, base_path+rad_file_name)
    print("Radiation file created: %s" % rad_file_name)

    #Input-Output flow
    print("Searching flow data")
    print("Getting data")

    #Uniform output
    out_dic = {1: {'Name':'Presa','Flow': 0.5}}
    presa_bct = 'Presa.bct'
    #input_csv = 'data/'
    #csv_to_bct(out_dic,presa_bct,input_csv,ini_date,end_date)
    modeling_file.gen_uniform_output_bct(out_dic,base_path+presa_bct,ini_date,end_date)

    out_dic = {1: {'Name':'Presa','Temperature': 12.5, 'Salinity': 0.03}}
    presa_bcc = 'Presa.bcc'
    modeling_file.gen_uniform_output_bcc(out_dic,base_path+presa_bcc,ini_date,end_date)

    input_dic = {1: {'Name': 'Duero', 'Flow': 0.4, 'Temperature': 12.5, 'Salinity': 0.03}, 2: {'Name': 'Revinuesa', 'Flow': 0.4, 'Temperature': 12.5, 'Salinity': 0.03}, 3: {'Name':'Ebrillos', 'Flow': 0.4, 'Temperature': 12.5, 'Salinity': 0.03}, 4: {'Name': 'Dehesa', 'Flow': 0.4, 'Temperature': 12.5, 'Salinity': 0.03}, 5: {'Name': 'Remonicio', 'Flow': 0.4, 'Temperature': 12.5, 'Salinity': 0.03}}
    input_dis = 'tributaries.dis'
    #input_dis_csv_folder = 'data/'
    #try:
    #    csv_to_dis(input_dic,input_dis_csv_folder,input_dis,ini_date,end_date)
    #except:
    modeling_file.gen_uniform_intput_dis(input_dic,base_path+input_dis,ini_date,end_date)

    #Parameters update
    dic = {'Itdate': "#"+ini_date.strftime('%Y-%m-%d')+"#\n", 
           'Tstart': "%i\n" % modeling_file.minutes_between_date(datetime.strptime(ini_date.strftime('%Y-%m-%d'),'%Y-%m-%d'),ini_date), 
           'Tstop': "%i\n" % modeling_file.minutes_between_date(ini_date,end_date),
           'Filwnd': "#" + wind_file_name + "#\n",
           'Filtmp': "#" + rad_file_name + "#\n",
           'FilbcT': "#" + presa_bct + "#\n",
           'FilbcC':"#" + presa_bcc + "#\n",
           'Fildis': "#" + input_dis + "#\n",           
           'Flmap' : "0 360 %i" % modeling_file.minutes_between_date(ini_date,end_date),
           'Zeta0' : "0\n"
          }
    #Update params
    modeling_file.update_param_value(dic,f1,f2)

    f1.close()

    #f1 = open(base_path+'test_1.mdf','r')
    #f2 = open(base_path+'test_1_v2.mdf','w')
    os.rename(base_path+'test_1.mdf', base_path+'test_old.mdf')
    os.rename(base_path+'test_1_v2.mdf',base_path+'test_1.mdf')
    
    # WATER QUALITY
    ini_date_str = start_date.strftime('%Y/%m/%d') + '-00:00:00'
    end_date_str = end_date.strftime('%Y/%m/%d')+'-00:00:00'


    q1 = open(base_path+'test_1.inp','r')
    q2 = open(base_path+'test_1_v2.inp','w')

     #TODO 
    wind_data = ini_date_str + '  2.55\n' + end_date_str + '  1.55\n'
    rad_data = ini_date_str + '  255.5\n' + end_date_str + '  155.5\n'


     #Layers
    k = 35
    #Check Wind file
    print("Searching Wind data")
    print("Getting data")
    wind_block = False
    rad_block = False
    for line in q1:
        if wind_block==False and rad_block==False:
            if '2012.01.02 00:00:00' in line:
                line = line.replace('2012.01.02',start_date.strftime('%Y')+'.'+start_date.strftime('%m') + '.' + start_date.strftime('%d'))
            if '2012/01/02-00:00:00' in line:
                line = line.replace('2012/01/02-00:00:00',ini_date_str)
            if '2012/01/05-00:00:00' in line:
                line = line.replace('2012/01/05-00:00:00',end_date_str)
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

    os.rename(base_path+'test_1.inp', base_path+'test_old.inp')
    os.rename(base_path+'test_1_v2.inp',base_path+'test_1.inp')
    
    try:
        deployment_id = launch_orchestrator_job('hydro',region+'/model_'+start_date.strftime('%Y-%m-%d')+'_'+end_date.strftime('%Y-%m-%d')+'/')
    except:
        print("PaaS Orchestrator disconnected. Run the model manually")
        return path+region+'/model_'+start_date.strftime('%Y-%m-%d')+'_'+end_date.strftime('%Y-%m-%d')+'/'
    
    return deployment_id
    
def temp_map(file, ini_date, end_date, z):

    dataset_map =  Dataset(file)
    sd = datetime.strptime(ini_date, '%Y-%m-%d %H:%M:%S')
    ed = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
    delta_time = (ed-sd).total_seconds()

    layer = int(((-z+35)/38)*35)

    if (delta_time/21600).is_integer:
        time = (delta_time/21600)

        temp_map = dataset_map.variables["R1"][time][1][layer][:][:]
        temp_map = np.ma.masked_where(temp_map <= 0, temp_map)
        plt.figure(1,figsize = (20,15))
        plt.imshow(np.flip(temp_map.transpose(),0),aspect='auto')
        plt.colorbar()
        plt.xlabel('lon')
        plt.ylabel('lat')
        plt.title("Map Temp {}, prof = {} meters".format(end_date, z))
        plt.show()
        
def get_access_token(url):
    if url is None:
        url = 'https://iam.extreme-datacloud.eu/token'
    #TODO manage exceptions
    access_token = os.environ['OAUTH2_AUTHORIZE_TOKEN']
    refresh_token = os.environ['OAUTH2_REFRESH_TOKEN']

    IAM_CLIENT_ID = os.environ['IAM_CLIENT_ID']
    IAM_CLIENT_SECRET = os.environ['IAM_CLIENT_SECRET']

    data = {'refresh_token': refresh_token, 'grant_type': 'refresh_token', 'client_id':IAM_CLIENT_ID, 'client_secret':IAM_CLIENT_SECRET}
    headers = {'Content-Type': 'application/json'}
    url = url+"?grant_type=refresh_token&refresh_token="+refresh_token+'&client_id='+IAM_CLIENT_ID+'&client_secret='+IAM_CLIENT_SECRET

    r = requests.post(url, headers=headers) #GET token
    print("Rquesting access token: %s" % r.status_code) #200 means that the resource exists
    access_token = json.loads(r.content)['access_token']
    return access_token

def launch_orchestrator_job(model_type,model_path):

    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}

    tosca_file = ''
    if model_type == 'hydro':
        tosca_file = ".HY_MODEL.yml"

    with open(tosca_file, 'r') as myfile:
        tosca = myfile.read()

    data = {"parameters" : {   
                "cpus" : 1,
                "mem" : "4096 MB",
                "onedata_provider" : "cloud-90-147-75-163.cloud.ba.infn.it",
                "model_space_name" : "LifeWatch",
                "model_path" : model_path,
                "output_filenames" : "trim-test_1.nc",
                "onedata_zone" : "https://onezone.cloud.cnaf.infn.it",
                "input_config_file" : "config_d_hydro.xml"
                 },
            "template" : tosca
            }

    url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'
    r = requests.post(url, headers=headers,data=json.dumps(data)) #GET
    print("Status code: %s" % r.status_code) #200 means that the resource exists
    print(r.headers)
    txt = json.loads(r.text)
    print (json.dumps(txt, indent=2, sort_keys=True))
    #print(r.text)
    #print(r.reason)
    deployment_id = json.loads(r.content)['uuid']
    print("Deployment ID: %s" % deployment_id)
    return deployment_id

def launch_orchestrator_sat_job(start_date,end_date,region,sat_type,sat_path):

    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}

    tosca_file = '.SAT_DATA.yml'

    with open(tosca_file, 'r') as myfile:
        tosca = myfile.read()
    
    data = {"parameters" : {   
                "cpus" : 1,
                "mem" : "4096 MB",
                "onedata_provider" : "cloud-90-147-75-163.cloud.ba.infn.it",
                "sat_space_name" : "LifeWatch",
                "sat" : sat_type,
                "sat_path" : sat_path,
                "region" : region,
                "start_date" : start_date.strftime('%Y-%m-%d'),
                "end_date" : end_date.strftime('%Y-%m-%d'),
                "onedata_zone" : "https://onezone.cloud.cnaf.infn.it"
                 },
            "template" : tosca
            }

    url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'
    r = requests.post(url, headers=headers,data=json.dumps(data)) #GET
    print("Status code SAT: %s" % r.status_code) #200 means that the resource exists
    print(r.headers)
    txt = json.loads(r.text)
    print (json.dumps(txt, indent=2, sort_keys=True))
    #print(r.text)
    #print(r.reason)
    deployment_id = json.loads(r.content)['uuid']
    print("Deployment ID: %s" % deployment_id)
    return deployment_id
    
def orchestrator_job_status(deployment_id):
    #TODO manage exceptions
    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    url =  'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'+deployment_id
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}
    r = requests.get(url, headers=headers) #GET token
    print("Status code: %s" % r.status_code)
    txt = json.loads(r.text)
    print (json.dumps(txt, indent=2, sort_keys=True))
    #print(r.text)
    #print(r.reason)
    return r.content

def orchestrator_list_deployments(orchestrator_url):
    #TODO manage exceptions
    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    if orchestrator_url is None:
        orchestrator_url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/'
    
    url = orchestrator_url + 'deployments?createdBy=' + os.environ['JUPYTERHUB_USER'] + '@https://iam.extreme-datacloud.eu/'
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}
    r = requests.get(url, headers=headers) #GET
    return json.loads(r.content)['content']


#################### MENU ##################################
onedata_wid = widgets.Text(
    value='',
    placeholder='Onedata token',
    description='Onedata token:',
    disabled=False
)
onedata_wid.value = os.environ['ONECLIENT_AUTHORIZATION_TOKEN']

region_buttons = widgets.ToggleButtons(
    options=['CdP','Sanabria'],
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
    options=['meteo', 'water_mask', 'water_surface', 'cloud_mask', 'cloud_coverage', 'list_files', 'download_sat_data', 'model'],
    value=['meteo'],
    #rows=10,
    description='Actions',
    disabled=False
)
tab = VBox(children=[onedata_wid, region_buttons, ini_date, end_date, actions])

button = widgets.Button(
    description='Run',
)

last_model=''

out = widgets.Output()
@button.on_click
def plot_on_click(b):
    with out:
        clear_output()
        if actions.value[0] == 'meteo':
            plot_meteo(region_buttons,ini_date,end_date,actions)
        elif actions.value[0] == 'list_files':
            find_dataset_type(ini_date.value,end_date.value,'',onedata_wid.value)
        elif actions.value[0] == 'download_sat_data':
            launch_orchestrator_sat_job(ini_date.value,end_date.value,region_buttons.value,'Landsat8','/xdc_lfw_sat/datesets/')
        elif actions.value[0] == 'model':
            last_model=prepare_model(ini_date.value,end_date.value, region_buttons.value, '/home/jovyan/datasets/LifeWatch/',onedata_wid.value)
        else:
            plot_satellite(region_buttons,ini_date,end_date,actions)

vbox1 = VBox(children=[tab,button,out])
#Jobs
job_list=[]
for e in orchestrator_list_deployments(None):
    job_list.append('ID: ' + e['uuid'] + ' | Creation time: ' + e['creationTime'] + ' | Status: ' + e['status'])

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
        orchestrator_job_status(jb[jb.find('ID: ', 0)+len('ID: '):jb.find(' | ')])

vbox2 = VBox(children=[selection_jobs,button2,out2])

#Model visualization
onedata_token = os.environ['ONECLIENT_AUTHORIZATION_TOKEN']
models = find_models(onedata_token)
opt = []
for e in models:
    opt.append(e['key']['region']+'/model_'+e['key']['beginDate']+'_'+e['key']['endDate']+'/trim-test_1.nc')

selection = widgets.Select(
    options=opt,
    value=None,
    # rows=10,
    description='Models',
    layout=Layout(width='75%'),
    disabled=False
)

depth_wid = widgets.IntSlider(
    value=7,
    min=0,
    max=35,
    step=1,
    description='Test:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d'
)
button3 = widgets.Button(
    description='Show model output',
)

out3 = widgets.Output()

@button.on_click
def model_on_click(b):
    with out3:
        clear_output()
        for e in models:
            temp_map('/home/jovyan/datasets/LifeWatch/' + selection.value, e['key']['beginDate']+' 00:00:00', e['key']['endDate']+' 01:00:00', depth_wid.value)
            break


vbox3 = VBox(children=[selection,depth_wid,button3,out3])

#Menu
menu = widgets.Tab()
menu.children = [vbox1, vbox2, vbox3]
menu.set_title(0,'Data Ingestion')
menu.set_title(1,'Job status')
menu.set_title(2,'Model visualization')
