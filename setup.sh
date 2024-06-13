#!/bin/bash

if [ "$EUID" -ne 0 ]
then
    echo "Please use sudo -E to run this script"
    exit 1
fi

# Install python
apt update && apt install python3-pip -y && python3 -V && pip3 -V

# Install mysql
apt-get install mysql-server -y && systemctl start mysql.service
mysql -e "source db/create_db.sql"

# Install prerequisites
apt-get install libgl1 tesseract-ocr nginx redis supervisor -y 
pip3 install -r requirements_cpu.txt
python3 -m spacy download en

# Create models repo
mkdir -p models/spacy_tr
# Manually download spacy transformer models

# setup supervisor
cp ./supervisord.conf /etc/supervisor/conf.d/iee_backend.conf

# Run server
supervisorctl reread
supervisorctl update
supervisorctl start all