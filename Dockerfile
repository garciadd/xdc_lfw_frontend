#Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Ubuntu 16.04 (xenial) from 2017-07-23
# https://github.com/docker-library/official-images/commit/0ea9b38b835ffb656c497783321632ec7f87b60c
FROM jupyter/base-notebook:latest

MAINTAINER Fernando Aguilar <aguilarf@ifca.unican.es>

USER root

# Install pymysql
RUN  apt-get update && \
  #apt-get -y upgrade && \
  apt-get install -y --reinstall build-essential && \
  apt-get install -y unixodbc-dev  unixodbc-bin && \
  apt-get install -y python-dev && \
  apt-get install -y freetds-dev && \
  apt-get install -y curl python3-setuptools

RUN pip install --upgrade pip

#
## Install ftp and Faker 
RUN  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y ftp
#
RUN pip install opencv-python Faker

## Install openstack client for python3
RUN apt-get update
RUN apt-get install -y libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev

RUN apt-get install -y python python-pip python-tk

RUN apt-get update && \
    apt-get install -y libreadline-dev && \
 #   apt upgrade -y r-base r-base-dev && \
    apt update && \
    apt upgrade && \
    apt-get install -y g++  && \
    apt-get install -y build-essential && \
    apt-get install -y libxml2-dev

ENV PATH="/usr/bin:${PATH}"


##### Install tools for datamining ###
RUN /opt/conda/bin/pip install numpy scipy matplotlib scikit-learn pandas pillow seaborn

# New Version add lxml library
#
RUN apt-get install -y  libxml2-dev libxslt-dev

RUN apt-get update && apt-get install -y iputils-ping net-tools
RUN apt-get install gcc git build-essential mysql-client python3-setuptools libmysqlclient-dev python3-dev python3-numpy python3-pip libhdf5-serial-dev netcdf-bin libnetcdf-dev wget m4 -y

#libnetcdf11

#RUN wget ftp://ftp.gnu.org/gnu/m4/m4-1.4.10.tar.gz && \
#    tar -xvzf m4-1.4.10.tar.gz && \
#    cd m4-1.4.10 && \
#    ./configure --prefix=/usr/local/m4 && \
#    make && make install

RUN wget ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4.4.0.tar.gz && \
    tar -zxvf netcdf-4.4.0.tar.gz && \
    rm netcdf-4.4.0.tar.gz
RUN cd netcdf-4.4.0 && ./configure --disable-netcdf-4 --prefix=/usr/local && make && make install
ENV NETCDF_LIBS -I/usr/local/lib
ENV NETCDF_CFLAGS -I/usr/local/include
RUN apt-get install software-properties-common -y
RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable 
RUN apt-get update -y
RUN apt-get install libpnetcdf-dev gdal-bin python3-gdal libgdal20 rabbitmq-server -y
#TODO libgdal1i

#The following env variables will be passed thorugh the orchestrator
ENV WQ_REGION CdP
ENV WQ_START_DATE 01-01-2018
ENV WQ_END_DATE 18-01-2018
ENV WQ_ACTION cloud_coverage
ENV ONEDATA_TOKEN 'MDAxNWxvY2F00aW9uIG9uZXpvbmUKMDAzMGlkZW500aWZpZXIgMDRmMGQxODRmMTBmODAxN2ZkNTNkNGJlYWIyNjc3NTkKMDAxYWNpZCB00aW1lIDwgMTU2MzM00NDg00MQowMDJmc2lnbmF00dXJlIGy97Y8H4rGIxCMYsJSHQg1v6BpLGAwnDL01EE6AFAs1BCg'
ENV ONEDATA_URL 'https://oneprovider-cnaf.cloud.cnaf.infn.it'
ENV ONEDATA_API '/api/v3/oneprovider/'
ENV ONEDATA_SPACE LifeWatch
ENV ONEDATA_ZONE 'https://onezone.cloud.cnaf.infn.it'
ENV DOWNLOAD_FOLDER datasets
RUN ls
RUN echo 'Cloning'
#The following env variables will be passed thorugh the orchestrator
# todoRUN pip3 install Cython

# && \
#    pip3 install -r requirements.txt && \
#    python3 setup.py install

WORKDIR $HOME

RUN exec 3<> /etc/apt/sources.list.d/onedata.list && \
    echo "deb [arch=amd64] http://packages.onedata.org/apt/ubuntu/xenial xenial main" >&3 && \
    echo "deb-src [arch=amd64] http://packages.onedata.org/apt/ubuntu/xenial xenial main" >&3 && \
    exec 3>&-
RUN curl http://packages.onedata.org/onedata.gpg.key | apt-key add -
RUN apt-get update && curl http://packages.onedata.org/onedata.gpg.key | apt-key add -
#USER $NB_USER
RUN easy_install request
RUN echo "test"
RUN conda install xmltodict scikit-image imageio netCDF4 tqdm numpy utm matplotlib pandas ipywidgets tornado=5.1.1 gdal -y
RUN jupyter nbextension enable --py --sys-prefix widgetsnbextension
#conda install skimage
RUN echo "Let's demo review or second"
RUN ls
RUN git clone https://github.com/IFCA/xdc_lfw_data.git
#Create config file

RUN exec 3<> ./xdc_lfw_data/wq_modules/config.py && \
    echo "#imports apis" >&3 && \
    echo "import os" >&3 && \
    echo "" >&3 && \
    echo "" >&3 && \
    echo "celery_db_user = \"root"\" >&3 && \
    echo "celery_db_pass = \"Yorick$$355"\" >&3 && \
    echo "" >&3 && \
    echo "#onedata mode" >&3 && \
    echo "onedata_mode = 1" >&3 && \
    echo "if onedata_mode == 1:" >&3 && \
    echo "" >&3 && \
    echo "    #onedata path and info" >&3 && \ 
    echo "    onedata_token = \"$ONEDATA_TOKEN\"" >&3 && \
    echo "    onedata_url = \"https://cloud-90-147-75-163.cloud.ba.infn.it\"" >&3 && \
    echo "    onedata_api = \"$ONEDATA_API\"" >&3 && \
    echo "    onedata_user = \"user\"" >&3 && \
    echo "    onedata_space = \"$ONEDATA_SPACE\"" >&3 && \
    echo "" >&3 && \
    echo "    #onedata path" >&3 && \
    echo "    datasets_path = \"/home/jovyan/datasets/LifeWatch\"" >&3 && \
    echo "" >&3 && \
    echo "#local path and info" >&3 && \ 
    echo "local_path = \"/home/jovyan/lfw_datasets\"" >&3 && \
    echo "" >&3 && \
    echo "#AEMET credentials" >&3 && \
    echo "METEO_API_TOKEN='eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ2aWxsYXJyakB1bmljYW4uZXMiLCJqdGkiOiJkZDc5ZjVmNy1hODQwLTRiYWQtYmMzZi1jNjI3Y2ZkYmUxNmYiLCJpc3MiOiJBRU1FVCIsImlhdCI6MTUyMDg0NzgyOSwidXNlcklkIjoiZGQ3OWY1ZjctYTg0MC00YmFkLWJjM2YtYzYyN2NmZGJlMTZmIiwicm9sZSI6IiJ9.LMl_cKCtYi3RPwLwO7fJYZMes-bdMVR91lRFZbUSv84'" >&3 && \
    echo "" >&3 && \
    echo "METEO_API_URL='opendata.aemet.es'" >&3 && \
    echo "" >&3 && \
    echo "#Sentinel credentials" >&3 && \
    echo "sentinel_pass = {'username':\"lifewatch\", 'password':\"xdc_lfw_data\"}" >&3 && \
    echo "" >&3 && \
    echo "#Landsat credentials" >&3 && \
    echo "landsat_pass = {'username':\"lifewatch\", 'password':\"xdc_lfw_data2018\"}" >&3 && \
    echo "" >&3 && \
    echo "#available regions" >&3 && \
    echo "regions = {'CdP': {\"id\": 210788, \"coordinates\": {\"W\":-2.830, \"S\":41.820, \"E\":-2.690, \"N\":41.910}}, 'Cogotas': {\"id\": 214571, \"coordinates\": {\"W\":-4.728, \"S\":40.657, \"E\":-4.672, \"N\":40.731}}, 'Sanabria': {\"id\": 211645, \"coordinates\": {\"W\":-6.739, \"S\":42.107, \"E\":-6.689, \"N\":42.136}}}"  >&3 && \
    echo "" >&3 && \
    echo "#available actions" >&3 && \
    echo "keywords = [\"cloud_mask\", \"cloud_coverage\", \"water_mask\", \"water_surface\", \"None\"]" >&3 && \
    exec 3>&-
#TODO earth engine api installation
RUN chown -R jovyan:users ./xdc_lfw_data
RUN cd ./xdc_lfw_data && \
    /opt/conda/bin/python setup.py install
RUN apt-get install sudo oneclient -y
RUN adduser jovyan sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN echo 'Frontend installing...'
RUN git clone https://github.com/IFCA/xdc_lfw_frontend
RUN chown -R jovyan:users ./xdc_lfw_frontend/*
RUN mv ./xdc_lfw_frontend/* /home/jovyan/
RUN mv ./xdc_lfw_frontend/.HY_MODEL.yml /home/jovyan/
RUN mv ./xdc_lfw_frontend/.SAT_DATA.yml /home/jovyan/
RUN mkdir datasets
ENV ONECLIENT_PROVIDER_HOSTNAME 'cloud-90-147-75-163.cloud.ba.infn.it'
RUN rm -rf work xdc_lfw_data netcdf-4.4.0 xdc_lfw_frontend
RUN chown -R jovyan:users ./test.sh
RUN chmod 777 test.sh
