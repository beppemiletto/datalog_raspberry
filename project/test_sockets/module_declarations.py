from construct import Struct,Const, Array, Byte, Int16ub,Int32ub
from datetime import timedelta
# Constants
BYTE_N = 32
SAMPLING_BASE_TIME = timedelta(0, 1,0)


# Structure for data exchange with sockets
MyDataFormat = Struct("Signature" / Const(b"BMS"), "time" / Int32ub, "data" / Array(BYTE_N, Int16ub), )

# Screen position of data
SCREEN_POS = [  (5, 2), (7, 2), (9, 2), (9, 2), (11, 2), (13, 2), (15, 2), (17, 2), (19, 2), (21, 2),
                (5, 27), (7, 27), (9, 27), (9, 27), (11, 27), (13, 27), (15, 27), (17, 27), (19, 27), (21, 27),
                (5, 52), (7, 52), (9, 52), (9, 52), (11, 52), (13, 52), (15, 52), (17, 52), (19, 52), (21, 52),
                (5, 77), (7, 77), (9, 77), (9, 77), (11, 77), (13, 77), (15, 77), (17, 77), (19, 77), (21, 77),
              ]