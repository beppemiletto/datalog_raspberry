#!/bin/bash


echo "start_backup.sh STARTING THE BACKUP PROCEDURE "
cd /home/pi/datalog_raspberry/project
python3 test_sockets/backup.py &&
echo "start_backup.sh ENDING THE BACKUP PROCEDURE"
exit 0
