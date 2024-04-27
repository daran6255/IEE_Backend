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
apt-get install libgl1 tesseract-ocr nginx -y 
pip3 install -r requirements_cpu.txt
python3 -m spacy download en

# Create models repo
mkdir -p models/spacy_tr
# Manually download spacy transformer models

# Run server
pm2 --name iee-backend start src/main.py