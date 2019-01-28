# -*- coding: utf-8 -*-
import socket
import os
import datetime, time
from module_declarations import MyDataFormat, SAMPLING_BASE_TIME, BYTE_N
import random

def rand_array_gen(length=1):
    array = []
    for i in range(length):
        array.append(random.randint(0, 65535))
    return array       
    

if os.path.exists("/home/beppe/project/test_sockets/python_unix_sockets_example"):
    os.remove("/home/beppe/project/test_sockets/python_unix_sockets_example")

print("Opening socket...")
server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind("/home/beppe/project/test_sockets/python_unix_sockets_example")


random.seed(int(time.time()))
print("Listening...")
server.listen(1)
print('-> server listening')
conn, addr = server.accept()
first_run = False

while True:

    #print('-> server datagram = conn.recv(16)')
    datagram = conn.recv(16)
    #print('-> server datagram = conn.recv(16)')
    if not datagram:
        break
    else:

        if "DONE" == datagram.upper().decode('utf-8'):
            break
        if not first_run:
            time_start = datetime.datetime.now()
            first_run=True
        elapsed_time = (datetime.datetime.now()-time_start).total_seconds()
        int_el_time = int(elapsed_time*10)
        data = rand_array_gen(length=BYTE_N)
        #print (data)
        mydata = MyDataFormat.build(dict(time= int_el_time, data=data))
        #print(MyDataFormat.parse(mydata))
        conn.send(mydata)

#print("-" * 40)
conn.close()
print("Connect Server Shutting down...")
server.close()
print("Server Shutting down...")
os.remove("/home/beppe/project/test_sockets/python_unix_sockets_example")
print("Done")