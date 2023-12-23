#!/bin/bash

systemctl.py enable mongod.service
systemctl.py start mongod
python expose_sftp.py