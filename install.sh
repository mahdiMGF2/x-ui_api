#! /bin/bash
echo "installing api"
git clone https://github.com/mahdigholipour3/x-ui_api.git
cd x-ui_api
sudo apt update;
sudo apt install python3-pip;
pip3 install -r requirements.txt;
clear;
echo "installed api";

 nohup python3 -u main.py
