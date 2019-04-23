from os import path, getcwd
from construct import Struct,Sequence ,Const, Array, Byte, Int16ub, Int16ul,Int32ub, Int32ul, Int32un, Int8ub, Float32l, PaddedString
from datetime import timedelta

# Running Environments
PC_OFFLINE = 0
RPI_PRODUCTION  = 1
RPI_DEVELOPMENT = 2

# DATA file directory
DATA_PATH = "/home/pi/DATA"

# Current working directory
CWD_PATH = getcwd()

# Socket dir end filenames
SKT_PATH = path.join(CWD_PATH,"sockets")
SKT_PL1000 = "PL1000.socket"
SKT_TC08 = "TC08.socket"
SKT_PEAK = "PEAK.socket"

# Hardware devices sn and enable

HW_SN_EN = {
    "PL1000": {"sn": "GT974/096", "en": True, "socket_file": SKT_PL1000},
    "TC08": {"sn": "A0061/874", "en": True , "socket_file": SKT_TC08},
    "PEAK": {"sn": "PEAK", "en": True,  "socket_file": SKT_PEAK},

}

# Constants
BYTE_N = 16
SAMPLING_BASE_TIME = timedelta(0, 0,1000000)


# Structure for data exchange with sockets
MyDataFormat = Struct("Signature" / Const(b"BMS"), "time" / Int32ub, "data" / Array(BYTE_N, Int16ub), )
# Structure for data exchange with sockets PL1012 Picolog
PL1012BYTE_N = 12
PL1012DataFormat = Struct("data" / Array(PL1012BYTE_N, Int16ul) )
TC08FLOAT_N = 9
TC08DataFormat = Struct("data" / Array(TC08FLOAT_N,Float32l))
PEAK_MSGS = 25
CANREAD_TIMEOUT = 0.600000
PEAKDataFormat = Array(PEAK_MSGS, Sequence(PaddedString(11, 'utf-8'), Array(8, Int8ub)))



# Screen position of data
SCREEN_POS = [ (5, 2), (7, 2), (9, 2), (11, 2), (13, 2), (15, 2), (17, 2), (19, 2), (21, 2), (23, 2),
                (5, 27), (7, 27), (9, 27), (11, 27), (13, 27), (15, 27), (17, 27), (19, 27), (21, 27), (23, 27),
                (5, 52), (7, 52), (9, 52), (11, 52), (13, 52), (15, 52), (17, 52), (19, 52), (21, 52), (23, 52),
                (5, 77), (7, 77), (9, 77), (11, 77), (13, 77), (15, 77), (17, 77), (19, 77), (21, 77), (23, 77),
               (25,2)
               ]