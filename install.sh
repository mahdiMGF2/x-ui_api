#! /bin/bash
echo "installing api"
git clone https://github.com/mahdigholipour3/x-ui_api.git
cd x-ui_api
sudo apt update;
sudo apt install python3-pip;
clear;
pip install -r requirements.txt;
read -p "Enter IP Address: " ip;
uvicorn main:app --host $ip --port 8000 --reload

