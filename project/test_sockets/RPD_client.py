# -*- coding: utf-8 -*-
import socket
import os, sys
from module_declarations import PL1012DataFormat, PL1012BYTE_N, SAMPLING_BASE_TIME, SCREEN_POS, BYTE_N, CWD_PATH
from module_declarations import SKT_PATH, SKT_PL1000, SKT_TC08, HW_SN_EN, TC08DataFormat, TC08FLOAT_N, PEAKDataFormat
from module_declarations import PC_OFFLINE, RPI_DEVELOPMENT, RPI_PRODUCTION
import time
import datetime
import xml.etree.ElementTree
import csv
import threading


# Class for thread running a blinking of PowerStatus LED
class BlinkPowerLed (threading.Thread):
    def __init__(self, thread_id, name, counter):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.counter = counter

    def run(self):
        print("Starting " + self.name)
        while power_latch:
            set_power_led(LED_OFF)
            time.sleep(0.25)
            set_power_led(LED_ON)
            time.sleep(0.25)
        print("Exiting " + self.name)


# Class for thread running a blinking of PowerStatus LED
class BlinkLoggingLed (threading.Thread):
    def __init__(self, thread_id, name, counter):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.counter = counter

    def run(self):
        print("Starting " + self.name)
        while logging_led_status:
            set_logging_led(LED_OFF)
            time.sleep(0.5)
            set_logging_led(LED_ON)
            time.sleep(0.5)
        print("Exiting " + self.name)


# Function for printing in Screen Matrix the displayed values
#
def print_xy(x, y, contents=None, color=None):
    sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, contents))
    sys.stdout.flush()


# Function for detecting the Key status from RPI GPIO
# The key status is connected to Raspberry GPIO 3
def key_status():
    key_status_detected = GPIO.input(3)
    return key_status_detected


# Function for setting the power status indicator LED mode
# The power status indicator LED is connected to Raspberry GPIO 9
def set_power_led(status):
    GPIO.output(9,status)


# Function for setting the logging status indicator LED mode
# The logging status indicator LED is connected to Raspberry GPIO 7
def set_logging_led(status):
    GPIO.output(7,status)
    return status


# Function for setting the power latch enable mode
# The power latch enable  is connected to Raspberry GPIO 5
def set_power_latch(status):
    GPIO.output(5,status)
    return status


# Function for linearize signal before writing records to CSV file
def linearise_signal(raw_value,parameters):
    linearized_value = None
    if parameters['hw'] == "pl1012":
        linearized_value = raw_value*float(parameters['slope'])+float(parameters['offset'])
    if parameters['hw'] == "pcan":
        resolution = float(parameters['resolution'])
        offset = float(parameters['offset'])
        if int(parameters['bits']) == 8 and int(parameters['bit_offset']) == 0:
            try:
                linearized_value = float(raw_value[0])*resolution+offset
            except:
                print("\n8  bits raw_value not convertible ='{}'".format(raw_value))
                print("for parameter ='{}'\n".format(parameters))
                linearized_value= None
        elif int(parameters['bits']) == 16 and int(parameters['bit_offset']) == 0:
            try:
                lsbyte = float(raw_value[0])
                msbyte = float(raw_value[1])
                raw_value_int = lsbyte+msbyte*2**8
                linearized_value = float(raw_value_int)*resolution+offset
            except:
                print("\n16 bits raw_value not convertible ='{}'".format(raw_value))
                print("for parameter ='{}'\n".format(parameters))
                linearized_value= None
        else:
            #TODO CAN linearization for data lenth less than 8 bits
            print("\nno 8 and no 16  bits raw_value not convertible ='{}'".format(raw_value))
            print("for parameter ='{}'\n".format(parameters))
            linearized_value = None

    return linearized_value


# Function sending command to Sockets client
def send_command(socket_client=None,command=None):
    bcommand = command.encode('utf-8')
    socket_client.send(bcommand)


environment = PC_OFFLINE

if environment == PC_OFFLINE:
    bt = SAMPLING_BASE_TIME.total_seconds()
    sleep_time = bt
    lag_correction = 0.0
    full_connect= False
    from RPiSim.GPIO import GPIO


elif environment == RPI_PRODUCTION:
    bt = SAMPLING_BASE_TIME.total_seconds()
    sleep_time = bt
    lag_correction = 0.0
    full_connect = False

GPIO.setmode(GPIO.BCM)
KEY_ON = True
KEY_OFF = False
LED_ON = GPIO.HIGH
LED_OFF = GPIO.LOW

GPIO.setup(3, GPIO.IN, initial=GPIO.HIGH, pull_up_down=GPIO.PUD_UP)     # this is the key sense input
GPIO.setup(5, GPIO.OUT, initial=GPIO.HIGH, pull_up_down=GPIO.PUD_DOWN)   # this the power latch enable output
logging_led_status = GPIO.LOW
GPIO.setup(7, GPIO.OUT, initial=logging_led_status, pull_up_down=GPIO.PUD_DOWN)  # this is the Datalogging running blinking led
GPIO.setup(9,GPIO.OUT, initial=GPIO.LOW, pull_up_down=GPIO.PUD_DOWN)   # this is the power state led output

if key_status() == KEY_ON:
    set_power_led(GPIO.HIGH)
    power_latch = set_power_latch(GPIO.HIGH)

else:
    set_power_led(GPIO.LOW)
    sys.exit(2)


#TODO develop the LED blinking and fixed
#TODO develop the power latch management


# calculates required connections total number
total_connection_req_conf = 0
for item in iter(HW_SN_EN):
    print(item)
    if HW_SN_EN[item]["en"]:
        total_connection_req_conf += 1
print("Connecting... looking for {} devices.".format(total_connection_req_conf))

time_conn_begin = datetime.datetime.now()
total_connection_req_det = 0
# Create clients for the three sockets
# Create PL1012 socket client
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
        print("something's wrong. Exception is %s" % (e))
        answ = "None"
    finally:
        print("Answer from server PL1012 socket: {}".format(answ))
        print("Ready.")
        # print("Ctrl-C to quit.")
        # print("Sending 'DONE' shuts down the server and quits.")

# Create TC08 socket client
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

# Create PCAN socket client
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


#  Parsing channels configuration from xml file
# BEGIN
tree = xml.etree.ElementTree.parse(os.path.join(CWD_PATH, 'conf/channel_config.xml'))
root = tree.getroot()
channels_dict = dict()
data_row = [None]
for type in root:
    print(type.tag, '<-- child.tag | child.attrib --->', type.attrib)
    if type.tag == 'DatalogFilenamePrefix':
        FILENAME_PREFIX = type.attrib['prefix']
    for ch in type.iter('ch'):
        channels_dict[ch.attrib['col']] = ch.attrib
        data_row.append(None)
        print(type.attrib['type'], ' -->  Analog input channels --> ', ch.attrib)

del root, tree, type, ch
# END OF CHANNELS CONFIG PARSER

#TODO write the csv writer for file container of data
file_name_suffix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
file_name = FILENAME_PREFIX+file_name_suffix+'.csv'
csv_file_name = os.path.join(CWD_PATH,file_name)
csv_file_header= open(csv_file_name,mode='w', encoding='utf-8')
csv_file = csv.writer(csv_file_header, dialect='excel', delimiter=',', quotechar="'", quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
del file_name, file_name_suffix, FILENAME_PREFIX

# write the file table columns header
head_row = list(' '*(len(channels_dict)+1))
# add first column as timestamp in position 0 (zero)
head_row[0]='Timestamp(Unix) [s from 1.1.1970]'
for col, channel in channels_dict.items():
    col_head = "{} [{}]".format(channel['name'],channel['um'])
    head_row[int(col)]=col_head
csv_file.writerow(head_row)

del head_row, col_head


# MAIN LOOP OF DATA LOGGING
first_cycle = True
#check the staus of the Key input - if KEY_OFF jump to program exit
while key_status() == KEY_ON:
    try:
        #for cycle in range(cycles):
        if first_cycle:

            # Create new threads
            thread2 = BlinkLoggingLed(2, "Blink-LogLed", 1)
            logging_led_status = True
            # Start new Threads
            thread2.start()


            t_old = datetime.datetime.now()
            iet = datetime.timedelta(0)
            et_mean=datetime.timedelta(0)

            send_command(client_PL1012, 'K')
            answ = ""

            send_command(client_TC08, 'S')
            answ_tc08 = ""
            cycle = 1
            first_cycle=False

        else:
            answ = client_PL1012.recv(24)

            answ_tc08 = client_TC08.recv(256)

            send_command(client_PEAK, 'S')
            answPEAK = client_PEAK.recv(2048)

            CAN_row_Data = []
            CAN_row_Data_parser = csv.reader(answPEAK.decode().split('\n'), delimiter=',')
            for value in CAN_row_Data_parser:
                CAN_row_Data.append(value)
                print('\t'.join(value))

            temperatures_data = TC08DataFormat.parse(answ_tc08)

            pl1012_data = PL1012DataFormat.parse(answ)

            # for i in range(TC08FLOAT_N):
            #
            #
            # for i in range(PL1012BYTE_N):
            #     print_xy(SCREEN_POS[i][0], SCREEN_POS[i][1] + 12, "{:06d}".format(data.data[i]))
            # for i in range(PL1012BYTE_N, PL1012BYTE_N + TC08FLOAT_N):
            #     print_xy(SCREEN_POS[i][0], SCREEN_POS[i][1] + 12,
            #              "{:04.3f}".format(temperatures.data[i - PL1012BYTE_N]))
            #
            # start_time_data = PL1012BYTE_N + TC08FLOAT_N + 1
            # # print_xy(SCREEN_POS[start_time_data][0], SCREEN_POS[start_time_data][1]+12, "{}".format(i))
            # print_xy(SCREEN_POS[start_time_data + 1][0], SCREEN_POS[start_time_data + 1][1] + 12,
            #          "cycle {}/{}".format(cycle, cycles))
            # print_xy(SCREEN_POS[start_time_data + 2][0], SCREEN_POS[start_time_data + 2][1] + 12,
            #          "Mean {:09.6f}".format(et_mean.total_seconds()))
            # print_xy(SCREEN_POS[start_time_data + 3][0], SCREEN_POS[start_time_data + 3][1] + 12,
            #          "Min {:09.6f}".format(et_min.total_seconds()))
            # print_xy(SCREEN_POS[start_time_data + 4][0], SCREEN_POS[start_time_data + 4][1] + 12,
            #          "Max {:09.6f}".format(et_max.total_seconds()))
            # print_xy(SCREEN_POS[start_time_data + 5][0], SCREEN_POS[start_time_data + 5][1] + 12,
            #          "Lag corr {:09.6f}".format(lag_correction))
            cycle +=1
            t_now = datetime.datetime.now()
            et = t_now -t_old
            iet += et
            et_mean= iet/cycle
            #print("SENT {} on iteration {}: et_mean={}, et_max= {}  et_min= {}".format(x, i, et_mean.total_seconds(),et_max.total_seconds(), et_min.total_seconds()))
            t_old=t_now
            lag_time = et.total_seconds()-bt
            lag_correction += lag_time/10

            sleep_time = bt - lag_correction
            # print_xy(SCREEN_POS[start_time_data+6][0], SCREEN_POS[start_time_data+6][1]+12, "Sleep time{}".format(sleep_time))

            send_command(client_PL1012,'K')

            send_command(client_TC08,'S')

            # Loop for data linearization according to channel_config.xml
            for col, channel in channels_dict.items():
                if channel['hw']=='tc08':
                    # TC08 return float value already linearized
                    data_row[int(col)] = temperatures_data.data[int(channel['ph'])]

                elif channel['hw']=='pl1012':
                    data_row[int(col)] = linearise_signal(pl1012_data.data[int(channel['ph'])],channel)
                elif channel['hw']=='pcan':
                    for msg in CAN_row_Data:
                        if len(msg) > 1:
                            msg_id = msg[0]
                            if channel['pgn'] in msg_id.upper():
                                data_len = int((float(channel['bits'])+7)/8)
                                data_row[int(col)] = linearise_signal(msg[int(channel['byte']):int(channel['byte'])+data_len],channel)
                else:
                    data_row[int(col)] = None

            # write the data row in csv file
            # insert timestamp
            data_row[0] = datetime.datetime.now(datetime.timezone.utc).timestamp()
            csv_file.writerow(data_row)

            if sleep_time < 0.0:
                sleep_time = bt
            time.sleep(sleep_time)


    except KeyboardInterrupt as k:
        print("\nClient Shutting down.\n")
        client_PL1012.close()
        client_TC08.close()
        client_PEAK.close()

        break

# send closing command and close all clients
print("\nClient Shutting down.\n")

logging_led_status = False
time.sleep(2)

# Create new threads
thread1 = BlinkPowerLed(1, "Thread-1", 1)

# Start new Threads
thread1.start()
print ("Exiting Main Thread")

send_command(client_PL1012, 'X')
client_PL1012.close()

send_command(client_TC08, 'X')
client_TC08.close()

send_command(client_PEAK, 'X')
client_PEAK.close()

GPIO.cleanup()

csv_file_header.close()

power_latch = False
thread1.join()
time.sleep(5)
set_power_latch(GPIO.LOW)


sys.exit(0)
