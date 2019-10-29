#!/bin/bash
rm -f function.zip
if [[ ! -d "./v-env" ]]; then 
	python3 -m venv v-env
	source v-env/bin/activate
	pip3 install gps
	pip3 install greengrasssdk
	deactivate
fi
cd v-env/lib/python3.7/site-packages
zip -r9 ${OLDPWD}/function.zip .
cd $OLDPWD
zip -g function.zip lambda_function.py
