#!/bin/bash

rm -rf venv/
virtualenv -p python3 venv
./venv/bin/pip install -r requirements.txt
echo "Copy config_example.py as config.py and update your username, password and waiting times between pages (and if needed update urls)."
echo "Execute ./run.sh to download your invoices. If you want to download specific amount of invoices, run the script with number. (e.g: ./run.sh 5)"
