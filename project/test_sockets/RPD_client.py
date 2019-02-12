# -*- coding: utf-8 -*-
import socket
import os, sys
from module_declarations import PL1012DataFormat, PL1012BYTE_N, SAMPLING_BASE_TIME, SCREEN_POS, BYTE_N, CWD_PATH, \
                                SKT_PATH, SKT_PL1000, SKT_TC08, HW_SN_EN
import time, datetime

def print_xy(x,y,contents=None,color=None):
    sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, contents))
    sys.stdout.flush()

cycles= 10
bt = SAMPLING_BASE_TIME.total_seconds()
sleep_time =bt
lag_correction = 0.0
full_connect= False




# calculates required connections total number
total_connection_req_conf = 0
for item in iter(HW_SN_EN):
    print(item)
    if HW_SN_EN[item]["en"]:
        total_connection_req_conf =+ 1
print("Connecting... looking for {} devices.".format(total_connection_req_conf))

time_conn_begin = datetime.datetime.now()_
while not(full_connect):

    if os.path.exists(os.path.join(SKT_PATH,SKT_PL1000)):
        client_PL1012 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_PL1012.connect(os.path.join(SKT_PATH,SKT_PL1000))
        answ = client_PL1012.recv(80)
        print("Answer from server PL1012 socket: {}".format(answ))
        print("Ready.")
        print("Ctrl-C to quit.")
        print("Sending 'DONE' shuts down the server and quits.")

    if os.path.exists(os.path.join(SKT_PATH, SKT_TC08)):
        client_TC08 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_TC08.connect(os.path.join(SKT_PATH, SKT_TC08))
        answ = client_TC08.recv(80);
        print("Answer from server TC08 socket: {}".format(answ))
        print("Ready.")
        print("Ctrl-C to quit.")
        print("Sending 'DONE' shuts down the server and quits.")



    _=os.system("clear")
    sys.stdout.flush()

    print("\n" * 40)
    # for i in range(BYTE_N):
    #     print_xy(SCREEN_POS[i][0],SCREEN_POS[i][1],"Dato {} =".format(i+1))
    print_xy(SCREEN_POS[BYTE_N + 1][0], SCREEN_POS[BYTE_N + 1][1], "{}".format('Time'))
    print_xy(SCREEN_POS[BYTE_N + 2][0], SCREEN_POS[BYTE_N + 2][1], "{}".format('et_mean'))
    print_xy(SCREEN_POS[BYTE_N + 3][0], SCREEN_POS[BYTE_N + 3][1], "{}".format('et_min'))
    print_xy(SCREEN_POS[BYTE_N + 4][0], SCREEN_POS[BYTE_N + 4][1], "{}".format('et_max'))
    print_xy(SCREEN_POS[BYTE_N + 5][0], SCREEN_POS[BYTE_N + 5][1], "{}".format('lag_time'))


    while True:
        try:
            x = input("> ")
            if "" != x:
                if "DONE" == x.upper():
                    print("Client Shutting down.")
                    x="X"
                    y = x+'\0'
                    by= y.encode('utf-8')
                    client_PL1012.send(by)
                    break
                for i in range(cycles):
                    if i == 0:
                        t_old = datetime.datetime.now()
                        iet = datetime.timedelta(0)
                        et_mean=datetime.timedelta(0)
                        et_min = datetime.timedelta(0, 3600, 0)
                        et_max = datetime.timedelta(0)
                    else:
                        t_now = datetime.datetime.now()
                        et = t_now -t_old
                        iet += et
                        et_mean= iet/i
                        et_min = min(et,et_min)
                        et_max = max(et,et_max)
                        #print("SENT {} on iteration {}: et_mean={}, et_max= {}  et_min= {}".format(x, i, et_mean.total_seconds(),et_max.total_seconds(), et_min.total_seconds()))
                        t_old=t_now
                        lag_time = et.total_seconds()-bt
                        lag_correction += lag_time/10

                        sleep_time = bt - lag_correction
                    y = x+'\0'
                    by= y.encode('utf-8')
                    client_PL1012.send(by)

                    answ= client_PL1012.recv(24)
                    # print("Server response received =",answ) #,MyDataFormat.parse(answ))
                    # print("-" * 60)
                    data = PL1012DataFormat.parse(answ)
                    for i in range(PL1012BYTE_N):
                         print_xy(SCREEN_POS[i][0], SCREEN_POS[i][1]+12, "{:06d}".format(data.data[i]))

                    print_xy(SCREEN_POS[PL1012BYTE_N][0], SCREEN_POS[PL1012BYTE_N][1]+12, "{}".format(i))
                    print_xy(SCREEN_POS[PL1012BYTE_N+1][0], SCREEN_POS[PL1012BYTE_N+1][1]+12, "{}".format(i))
                    print_xy(SCREEN_POS[PL1012BYTE_N+2][0], SCREEN_POS[PL1012BYTE_N+2][1]+12, "{:09.6f}".format(et_mean.total_seconds()))
                    print_xy(SCREEN_POS[PL1012BYTE_N+3][0], SCREEN_POS[PL1012BYTE_N+3][1]+12, "{:09.6f}".format(et_min.total_seconds()))
                    print_xy(SCREEN_POS[PL1012BYTE_N+4][0], SCREEN_POS[PL1012BYTE_N+4][1]+12, "{:09.6f}".format(et_max.total_seconds()))
                    print_xy(SCREEN_POS[PL1012BYTE_N+5][0], SCREEN_POS[PL1012BYTE_N+5][1]+12, "{:09.6f}".format(lag_correction))
                    print_xy(SCREEN_POS[PL1012BYTE_N+6][0], SCREEN_POS[PL1012BYTE_N+6][1]+12, "{}".format(answ))

                    if sleep_time < 0.0:
                        sleep_time=bt
                    time.sleep(sleep_time)
        except KeyboardInterrupt as k:
            print("Client Shutting down.")
            client_PL1012.close()
            break
else:
    print("Couldn't Connect!")
print("Client Done")
