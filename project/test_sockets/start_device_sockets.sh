#!/usr/bin/env bash

echo "Starting Pico and Peak Hardware's sockets processes for Datalogger"
echo "\nStarting Picolo PL1012"

cd ~/datalog_raspberry/project/sockets/

~/pico_sdk/pl1000/linux-build-files/pl1000Con PL1000096.socket &

echo "\n\nStarting Picolo PL1012"

sleep 3.5s

~/pico_sdk/usbtc08/linux-build-files/usbtc08Con TC08874.socket &

echo "\n\nStarting PCAN socket"
# source ~/venv/bin/activate


cd ~/datalog_raspberry/project/

pwd

python3 test_sockets/PCAN_server_socket.py &


sleep 3.5



cd ~/datalog_raspberry/project/test_sockets/

pwd


echo "All socket created"
##python RPD_client.py



