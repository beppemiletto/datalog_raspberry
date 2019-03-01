#!/usr/bin/env bash

echo "Starting Pico and Peak Hardware's sockets processes for Datalogger"
echo "\nStarting Picolo PL1012"

cd ~/project/datalog_raspberry/sockets/

~/project/picolog/picosdk-c-examples/pl1000/linux-build-files/pl1000Con PL1000096.socket &

echo "\n\nStarting Picolo PL1012"

sleep 2.5s

~/project/picolog/picosdk-c-examples/usbtc08/linux-build-files/usbtc08Con TC08874.socket &

source ~/project/venv/bin/activate


#cd ~/project/datalog_raspberry/project/test_sockets/

#pwd

#python PCAN_server_socket.py


sleep 2.5



cd ~/project/datalog_raspberry/project/test_sockets/

pwd


echo "All socket created"
##python RPD_client.py



