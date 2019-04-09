#!/bin/bash

echo "Starting Pico and Peak Hardware's sockets processes for Datalogger \n"

cd /home/pi/datalog_raspberry/project/sockets/

echo "\n\nStarting Picolog PL1012"
/home/pi/pico_sdk/pl1000/linux-build-files/pl1000Con PL1000.socket &
sleep 5

echo "\n\nStarting Picolog TC08"
/home/pi/pico_sdk/usbtc08/linux-build-files/usbtc08Con TC08.socket &
sleep 4

echo "\n\nStarting PCAN socket"


cd /home/pi/datalog_raspberry/project/

python3 test_sockets/PCAN_server_socket.py &


sleep 3

echo "All socket launched."


exit 0
