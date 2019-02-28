# -*- coding: utf-8 -*-
import socket
import os, sys
from module_declarations import PL1012DataFormat, PL1012BYTE_N, SAMPLING_BASE_TIME, SCREEN_POS, BYTE_N, CWD_PATH
from module_declarations import SKT_PATH, SKT_PL1000, SKT_TC08, HW_SN_EN, TC08DataFormat, TC08FLOAT_N, PEAKDataFormat
from module_declarations import  PC_OFFLINE, RPI_DEVELOPMENT, RPI_PRODUCTION
import time, datetime
import subprocess


environment = PC_OFFLINE

if environment == PC_OFFLINE:
    cycles= 10
    bt = SAMPLING_BASE_TIME.total_seconds()
    sleep_time =bt
    lag_correction = 0.0
    full_connect= False
    key_status = True
    from RPiSim.GPIO import GPIO
    GPIO.setmode(GPIO.BCM)



    KEY_ON = False
    KEY_OFF = True

elif environment == RPI_PRODUCTION:
    cycles= 21
    bt = SAMPLING_BASE_TIME.total_seconds()
    sleep_time =bt
    lag_correction = 0.0
    full_connect= False
    KEY_ON = True
    KEY_OFF = False

GPIO.setup(3, GPIO.IN, initial=GPIO.HIGH, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(5, GPIO.OUT, initial=GPIO.LOW, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(7, GPIO.OUT, initial=GPIO.HIGH, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(9,GPIO.OUT, initial=GPIO.HIGH, pull_up_down=GPIO.PUD_DOWN)

## Function for printing in Screen Matrix the displayed values
##
def print_xy(x,y,contents=None,color=None):
    sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, contents))
    sys.stdout.flush()


## Function for detecting the Key status from RPI GPIO
##
def KeyStatus():
    key_status = GPIO.input(3)
    return key_status






# calculates required connections total number
total_connection_req_conf = 0
for item in iter(HW_SN_EN):
    print(item)
    if HW_SN_EN[item]["en"]:
        total_connection_req_conf += 1
print("Connecting... looking for {} devices.".format(total_connection_req_conf))

time_conn_begin = datetime.datetime.now()
total_connection_req_det = 0

if HW_SN_EN["PL1000"]["en"]:
    try:
        # Starting C modules streaming sockets
        # Starting PL1000
        if os.path.exists(os.path.join(SKT_PATH,HW_SN_EN["PL1000"]["socket_file"])):
            client_PL1012 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_PL1012.connect(os.path.join(SKT_PATH,HW_SN_EN["PL1000"]["socket_file"]))
            answ = client_PL1012.recv(20)
            total_connection_req_det += 1
        else:
            answ = "socket file {} not found".format(os.path.join(SKT_PATH,HW_SN_EN["PL1000"]["socket_file"]))
    except Exception as e:
        print("something's wrong with %s:%d. Exception is %s" % (address, port, e))
        answ = "None"
    finally:
        print("Answer from server PL1012 socket: {}".format(answ))
        print("Ready.")
        # print("Ctrl-C to quit.")
        # print("Sending 'DONE' shuts down the server and quits.")

if HW_SN_EN["TC08"]["en"]:
    try:
        if os.path.exists(os.path.join(SKT_PATH, HW_SN_EN["TC08"]["socket_file"])):
            client_TC08 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_TC08.connect(os.path.join(SKT_PATH, HW_SN_EN["TC08"]["socket_file"]))
            answ = client_TC08.recv(20)
            total_connection_req_det += 1
        else:
            answ = "socket file {} not found".format(os.path.join(SKT_PATH,HW_SN_EN["PL1000"]["socket_file"]))

    except Exception as e:
        print("something's wrong with %s:%d. Exception is %s" % (address, port, e))
        answ = "None"
    finally:
        print("Answer from server TC08 socket: {}".format(answ))
        print("Ready.")
        print("Ctrl-C to quit.")
        print("Sending 'DONE' shuts down the server and quits.")

if HW_SN_EN["PEAK"]["en"]:
    try:
        if os.path.exists(os.path.join(SKT_PATH, HW_SN_EN["PEAK"]["socket_file"])):
            client_PEAK = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_PEAK.connect(os.path.join(SKT_PATH, HW_SN_EN["PEAK"]["socket_file"]))
            answ = client_PEAK.recv(20)
            total_connection_req_det += 1
        else:
            answ = "socket file {} not found".format(os.path.join(SKT_PATH, HW_SN_EN["PL1000"]["socket_file"]))

    except Exception as e:
        print("something's wrong with opening PEAK. Exception is %s " % (e))
        answ = "None"
    finally:
        print("Answer from server PEAK socket: {}".format(answ))
        print("Ready.")
        print("Ctrl-C to quit.")
        print("Sending 'DONE' shuts down the server and quits.")

    _=os.system("clear")
    sys.stdout.flush()

if total_connection_req_det != total_connection_req_conf:
    sys.exit(1)

else:

    print("\n" * 40)
    # for i in range(BYTE_N):
    #     print_xy(SCREEN_POS[i][0],SCREEN_POS[i][1],"Dato {} =".format(i+1))
    # print_xy(SCREEN_POS[BYTE_N + 1][0], SCREEN_POS[BYTE_N + 1][1], "{}".format('Time'))
    # print_xy(SCREEN_POS[BYTE_N + 2][0], SCREEN_POS[BYTE_N + 2][1], "{}".format('et_mean'))
    # print_xy(SCREEN_POS[BYTE_N + 3][0], SCREEN_POS[BYTE_N + 3][1], "{}".format('et_min'))
    # print_xy(SCREEN_POS[BYTE_N + 4][0], SCREEN_POS[BYTE_N + 4][1], "{}".format('et_max'))
    # print_xy(SCREEN_POS[BYTE_N + 5][0], SCREEN_POS[BYTE_N + 5][1], "{}".format('lag_time'))




    while KeyStatus() == KEY_ON:
        try:
            x = 'K'


            for cycle in range(cycles):
                if cycle == 0:
                    t_old = datetime.datetime.now()
                    iet = datetime.timedelta(0)
                    et_mean=datetime.timedelta(0)
                    et_min = datetime.timedelta(0, 3600, 0)
                    et_max = datetime.timedelta(0)
                    y = x + '\0'
                    by = y.encode('utf-8')
                    client_PL1012.send(by)
                    answ = ""

                    # PEAKch = "S".encode('utf-8')
                    # client_PEAK.send(PEAKch)
                    # answPEAK = ""

                    tc08ch = "S".encode('utf-8')
                    client_TC08.send(tc08ch)
                    answ_tc08 = ""
                else:
                    answ = client_PL1012.recv(24)

                    answ_tc08 = client_TC08.recv(256)

                    PEAKch = "S".encode('utf-8')
                    client_PEAK.send(PEAKch)
                    answPEAK = client_PEAK.recv(512)
                    CAN_row_Data = PEAKDataFormat.parse(answPEAK)


                    temperatures = TC08DataFormat.parse(answ_tc08)
                    # print("Server response received =",answ) #,MyDataFormat.parse(answ))
                    # print("-" * 60)
                    data = PL1012DataFormat.parse(answ)
                    for i in range(PL1012BYTE_N):
                        print_xy(SCREEN_POS[i][0], SCREEN_POS[i][1] + 12, "{:06d}".format(data.data[i]))
                    for i in range(PL1012BYTE_N, PL1012BYTE_N + TC08FLOAT_N):
                        print_xy(SCREEN_POS[i][0], SCREEN_POS[i][1] + 12,
                                 "{:04.3f}".format(temperatures.data[i - PL1012BYTE_N]))

                    start_time_data = PL1012BYTE_N + TC08FLOAT_N + 1
                    # print_xy(SCREEN_POS[start_time_data][0], SCREEN_POS[start_time_data][1]+12, "{}".format(i))
                    print_xy(SCREEN_POS[start_time_data + 1][0], SCREEN_POS[start_time_data + 1][1] + 12,
                             "cycle {}/{}".format(cycle, cycles))
                    print_xy(SCREEN_POS[start_time_data + 2][0], SCREEN_POS[start_time_data + 2][1] + 12,
                             "Mean {:09.6f}".format(et_mean.total_seconds()))
                    print_xy(SCREEN_POS[start_time_data + 3][0], SCREEN_POS[start_time_data + 3][1] + 12,
                             "Min {:09.6f}".format(et_min.total_seconds()))
                    print_xy(SCREEN_POS[start_time_data + 4][0], SCREEN_POS[start_time_data + 4][1] + 12,
                             "Max {:09.6f}".format(et_max.total_seconds()))
                    print_xy(SCREEN_POS[start_time_data + 5][0], SCREEN_POS[start_time_data + 5][1] + 12,
                             "Lag corr {:09.6f}".format(lag_correction))
                    t_now = datetime.datetime.now()
                    et = t_now -t_old
                    iet += et
                    et_mean= iet/cycle
                    et_min = min(et,et_min)
                    et_max = max(et,et_max)
                    #print("SENT {} on iteration {}: et_mean={}, et_max= {}  et_min= {}".format(x, i, et_mean.total_seconds(),et_max.total_seconds(), et_min.total_seconds()))
                    t_old=t_now
                    lag_time = et.total_seconds()-bt
                    lag_correction += lag_time/10

                    sleep_time = bt - lag_correction
                    print_xy(SCREEN_POS[start_time_data+6][0], SCREEN_POS[start_time_data+6][1]+12, "Sleep time{}".format(sleep_time))

                    y = x + '\0'
                    by = y.encode('utf-8')
                    client_PL1012.send(by)

                    tc08ch = "S".encode('utf-8')
                    client_TC08.send(tc08ch)


                    if sleep_time < 0.0:
                        sleep_time = bt
                    time.sleep(sleep_time)

            if cycle == cycles-1:
                print("Client Shutting down.")
                x="X"
                y = x+'\0'
                by= y.encode('utf-8')
                client_PL1012.send(by)
                client_PL1012.close()

                tc08ch= "X".encode('utf-8')
                client_TC08.send(tc08ch)
                client_TC08.close()

                client_PEAK.send('X'.encode('utf-8'))
                client_PEAK.close()

                GPIO.cleanup()

                break
        except KeyboardInterrupt as k:
            print("Client Shutting down.")
            client_PL1012.close()
            client_TC08.close()
            client_PEAK.close()

            break

if environment == PC_OFFLINE:
    GPIO.cleanup()
    del GPIO

sys.exit(0)