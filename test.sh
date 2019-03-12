#!/bin/bash
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
export OAUTH2_AUTHORIZE_TOKEN=$(curl -X POST -H "Content-Type: application/json" -s "https://iam.extreme-datacloud.eu/token?grant_type=refresh_token&refresh_token=$OAUTH2_REFRESH_TOKEN&client_id=$IAM_CLIENT_ID&client_secret=$IAM_CLIENT_SECRET" | python -c "import sys, json; print json.load(sys.stdin)['access_token']")
curl -H "X-Auth-Token: eXtreme-DataCloud:$OAUTH2_AUTHORIZE_TOKEN" -s "$ONEDATA_ZONE/api/v3/onezone/user/client_tokens"
export ONEDATA_TOKEN=$(curl -H "X-Auth-Token: eXtreme-DataCloud:$OAUTH2_AUTHORIZE_TOKEN" -s "$ONEDATA_ZONE/api/v3/onezone/user/client_tokens" | python -c "import sys, json; print json.load(sys.stdin)['tokens'][0]")
export ONECLIENT_AUTHORIZATION_TOKEN=$ONEDATA_TOKEN
sudo chown -R jovyan:users /home/jovyan/.local/share/jupyter
sudo chown -R jovyan:users /home/jovyan/datasets
su jovyan -c 'oneclient --authentication token --no_check_certificate /home/jovyan/datasets'
tini -g -- start-notebook.sh --ip="0.0.0.0" --port=8888
