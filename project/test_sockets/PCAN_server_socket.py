# -*- coding: cp1252 -*-
######################################################################
#  PCAN_server_socket.py
#  ~~~~~~~~~~~~
#  Author GM
#  Language: Python 3.5
#  ------------------------------------------------------------------
#  Original Author : Keneth Wagner
#  Language: Python 2.7
#  ------------------------------------------------------------------
#
#  Copyright (C) 1999-2017  PEAK-System Technik GmbH, Darmstadt
######################################################################

# Import modules
from PCANBasic import *        ## PCAN-Basic library import
import traceback               ## Error-Tracing library
import string                  ## String functions
import time                    ## Time-related library
import threading               ## Threading-based Timer library
import platform                ## Underlying platform’s info library
import sys

import socket
import os
import datetime
from module_declarations import SKT_PATH, SKT_PEAK, PEAK_MSGS, PEAKDataFormat, CANREAD_TIMEOUT



TCL_DONT_WAIT           = 1<<1
TCL_WINDOW_EVENTS       = 1<<2
TCL_FILE_EVENTS         = 1<<3
TCL_TIMER_EVENTS        = 1<<4
TCL_IDLE_EVENTS         = 1<<5
TCL_ALL_EVENTS          = 0


COL_TYPE = 0
COL_ID = 1
COL_LENGTH = 2
COL_COUNT = 3
COL_TIME = 4
COL_DATA = 5

IS_WINDOWS = platform.system() == 'Windows'
DISPLAY_UPDATE_MS = 100

# For Non Windows system

FRAME_WIDTH = 970
FRAME_HEIGHT = 730
GROUPBOX_WIDTH = 958
GROUPBOX_HEIGHT = 80
ENABLE_CAN_FD = False
# check driver version before enabling FD
try:
    with open("/sys/class/pcan/version") as f:
        version = f.readline()
        if (int(version[0]) >= 8):
            ENABLE_CAN_FD = True
except Exception:
    ENABLE_CAN_FD = False
WINDOWS_EVENT_SUPPORT = False


###*****************************************************************
### PCAN-basic Example app
###*****************************************************************
class PCANBasicExample(object):
    ## Constructor
    ##
    def __init__(self):

        # Example's configuration
        self.InitializeBasicComponents()
        self.InitializeSocket()
        self.ConfigureLogFile()
        self.btnHwRefresh_Click()
        self.btnInit_Click()
        self.SetConnectionStatus(True)
        self.AckSocket()
    ## Destructor
    ##
    def destroy(self):
        # close and cancel the socket
        self.server.close()
        try:
            os.remove(self.socket_file)
            print("Socket file {} successfully deleted!".format(self.socket_file))
            del self.socket_file
        except:
            print("Peak socket file not removed exception ")


    ## Main Loop of working
    def loop(self):
        ## Initialize the messages container
        ##
        stsResult = PCAN_ERROR_OK
        self.m_LastMsgsList = []
        while self.exit < 0:
            time_start = time.time()
            elapsedtime = time.time()-time_start
            while (not (stsResult & PCAN_ERROR_QRCVEMPTY)) and (len(self.m_LastMsgsList) < PEAK_MSGS) and elapsedtime < CANREAD_TIMEOUT:
                result = self.m_objPCANBasic.Read(self.m_PcanHandle)
                if result[0] == PCAN_ERROR_OK:
                    ProcessingMessage = result[1:]
                    theMsg = ProcessingMessage[0]
                    itsTimeStamp = ProcessingMessage[1]

                    newMsg = TPCANMsgFD()
                    newMsg.ID = theMsg.ID
                    newMsg.DLC = theMsg.LEN
                    for i in range(8 if (theMsg.LEN > 8) else theMsg.LEN):
                        newMsg.DATA[i] = theMsg.DATA[i]
                    newMsg.MSGTYPE = theMsg.MSGTYPE
                    newTimestamp = TPCANTimestampFD()
                    newTimestamp.value = (
                                itsTimeStamp.micros + 1000 * itsTimeStamp.millis + 0x100000000 * 1000 * itsTimeStamp.millis_overflow)
                    found = False
                    for (ID,DATA) in self.m_LastMsgsList:
                        if ID == newMsg.ID:
                            found= True
                    if not found:
                        #TODO select message incoming from list in xml config. Discarge unuseful messages
                        self.m_LastMsgsList.append((theMsg.ID, theMsg.DATA))
                    time.sleep(0.010)
                elapsedtime = time.time()-time_start

            response = ""
            for msg in self.m_LastMsgsList:
                response = response+"{:>10},{},{},{},{},{},{},{},{}\n".format(hex(msg[0]),msg[1][0],
                                                                    msg[1][1],
                                                                    msg[1][2],
                                                                    msg[1][3],
                                                                    msg[1][4],
                                                                    msg[1][5],
                                                                    msg[1][6],
                                                                    msg[1][7],
                                                                    )
            self.m_LastMsgsList=[]
            try:
                i = 0
                answ = self.conn.recv(1)
                if answ == b'S':
                    self.conn.send(response.encode('utf-8'))
                    self.btnReset_Click()
                elif answ == b'X':
                    print("Termination request received from client - Shutting down")
                    return
                else:
                    continue
            except SystemExit:
                # Tkinter uses SystemExit to exit
                self.exit = 1
                return
            except KeyboardInterrupt:
                print("Termination request for KeyboardInterrupt received - Shutting down")
                return
            except:
                # Otherwise it's some other error
                t, v, tb = sys.exc_info()
                text = ""
                for line in traceback.format_exception(t, v, tb):
                    text += line + '\n'
                try:
                    print('Error', text)
                except:
                    pass
                self.exit = 1
                # raise (SystemExit, 1)

    ################################################################################################################################################
    ### Help functions
    ################################################################################################################################################

    ## Initializes app members
    ##
    def InitializeBasicComponents(self):

        self.exit = -1
        self.m_objPCANBasic = PCANBasic()
        self.m_PcanHandle = PCAN_NONEBUS
        self.m_LastMsgsList = []

        self.m_IsFD = False
        self.m_CanRead = True

        self._lock = threading.RLock()

        self.m_CHANNELS = {'PCAN_DNGBUS1': PCAN_DNGBUS1, 'PCAN_PCCBUS1': PCAN_PCCBUS1, 'PCAN_PCCBUS2': PCAN_PCCBUS2,
                           'PCAN_ISABUS1': PCAN_ISABUS1,
                           'PCAN_ISABUS2': PCAN_ISABUS2, 'PCAN_ISABUS3': PCAN_ISABUS3, 'PCAN_ISABUS4': PCAN_ISABUS4,
                           'PCAN_ISABUS5': PCAN_ISABUS5,
                           'PCAN_ISABUS6': PCAN_ISABUS6, 'PCAN_ISABUS7': PCAN_ISABUS7, 'PCAN_ISABUS8': PCAN_ISABUS8,
                           'PCAN_PCIBUS1': PCAN_PCIBUS1,
                           'PCAN_PCIBUS2': PCAN_PCIBUS2, 'PCAN_PCIBUS3': PCAN_PCIBUS3, 'PCAN_PCIBUS4': PCAN_PCIBUS4,
                           'PCAN_PCIBUS5': PCAN_PCIBUS5,
                           'PCAN_PCIBUS6': PCAN_PCIBUS6, 'PCAN_PCIBUS7': PCAN_PCIBUS7, 'PCAN_PCIBUS8': PCAN_PCIBUS8,
                           'PCAN_PCIBUS9': PCAN_PCIBUS9,
                           'PCAN_PCIBUS10': PCAN_PCIBUS10, 'PCAN_PCIBUS11': PCAN_PCIBUS11,
                           'PCAN_PCIBUS12': PCAN_PCIBUS12, 'PCAN_PCIBUS13': PCAN_PCIBUS13,
                           'PCAN_PCIBUS14': PCAN_PCIBUS14, 'PCAN_PCIBUS15': PCAN_PCIBUS15,
                           'PCAN_PCIBUS16': PCAN_PCIBUS16, 'PCAN_USBBUS1': PCAN_USBBUS1,
                           'PCAN_USBBUS2': PCAN_USBBUS2, 'PCAN_USBBUS3': PCAN_USBBUS3, 'PCAN_USBBUS4': PCAN_USBBUS4,
                           'PCAN_USBBUS5': PCAN_USBBUS5,
                           'PCAN_USBBUS6': PCAN_USBBUS6, 'PCAN_USBBUS7': PCAN_USBBUS7, 'PCAN_USBBUS8': PCAN_USBBUS8,
                           'PCAN_USBBUS9': PCAN_USBBUS9,
                           'PCAN_USBBUS10': PCAN_USBBUS10, 'PCAN_USBBUS11': PCAN_USBBUS11,
                           'PCAN_USBBUS12': PCAN_USBBUS12, 'PCAN_USBBUS13': PCAN_USBBUS13,
                           'PCAN_USBBUS14': PCAN_USBBUS14, 'PCAN_USBBUS15': PCAN_USBBUS15,
                           'PCAN_USBBUS16': PCAN_USBBUS16, 'PCAN_LANBUS1': PCAN_LANBUS1,
                           'PCAN_LANBUS2': PCAN_LANBUS2, 'PCAN_LANBUS3': PCAN_LANBUS3, 'PCAN_LANBUS4': PCAN_LANBUS4,
                           'PCAN_LANBUS5': PCAN_LANBUS5,
                           'PCAN_LANBUS6': PCAN_LANBUS6, 'PCAN_LANBUS7': PCAN_LANBUS7, 'PCAN_LANBUS8': PCAN_LANBUS8,
                           'PCAN_LANBUS9': PCAN_LANBUS9,
                           'PCAN_LANBUS10': PCAN_LANBUS10, 'PCAN_LANBUS11': PCAN_LANBUS11,
                           'PCAN_LANBUS12': PCAN_LANBUS12, 'PCAN_LANBUS13': PCAN_LANBUS13,
                           'PCAN_LANBUS14': PCAN_LANBUS14, 'PCAN_LANBUS15': PCAN_LANBUS15,
                           'PCAN_LANBUS16': PCAN_LANBUS16}

        self.m_BAUDRATES = {'1 MBit/sec': PCAN_BAUD_1M, '800 kBit/sec': PCAN_BAUD_800K, '500 kBit/sec': PCAN_BAUD_500K,
                            '250 kBit/sec': PCAN_BAUD_250K,
                            '125 kBit/sec': PCAN_BAUD_125K, '100 kBit/sec': PCAN_BAUD_100K,
                            '95,238 kBit/sec': PCAN_BAUD_95K, '83,333 kBit/sec': PCAN_BAUD_83K,
                            '50 kBit/sec': PCAN_BAUD_50K, '47,619 kBit/sec': PCAN_BAUD_47K,
                            '33,333 kBit/sec': PCAN_BAUD_33K, '20 kBit/sec': PCAN_BAUD_20K,
                            '10 kBit/sec': PCAN_BAUD_10K, '5 kBit/sec': PCAN_BAUD_5K}

        self.m_HWTYPES = {'ISA-82C200': PCAN_TYPE_ISA, 'ISA-SJA1000': PCAN_TYPE_ISA_SJA,
                          'ISA-PHYTEC': PCAN_TYPE_ISA_PHYTEC, 'DNG-82C200': PCAN_TYPE_DNG,
                          'DNG-82C200 EPP': PCAN_TYPE_DNG_EPP, 'DNG-SJA1000': PCAN_TYPE_DNG_SJA,
                          'DNG-SJA1000 EPP': PCAN_TYPE_DNG_SJA_EPP}

        self.m_IOPORTS = {'0100': 0x100, '0120': 0x120, '0140': 0x140, '0200': 0x200, '0220': 0x220, '0240': 0x240,
                          '0260': 0x260, '0278': 0x278,
                          '0280': 0x280, '02A0': 0x2A0, '02C0': 0x2C0, '02E0': 0x2E0, '02E8': 0x2E8, '02F8': 0x2F8,
                          '0300': 0x300, '0320': 0x320,
                          '0340': 0x340, '0360': 0x360, '0378': 0x378, '0380': 0x380, '03BC': 0x3BC, '03E0': 0x3E0,
                          '03E8': 0x3E8, '03F8': 0x3F8}

        self.m_INTERRUPTS = {'3': 3, '4': 4, '5': 5, '7': 7, '9': 9, '10': 10, '11': 11, '12': 12, '15': 15}

        self.m_PARAMETERS = {'USBs Device Number': PCAN_DEVICE_NUMBER, 'USB/PC-Cards 5V Power': PCAN_5VOLTS_POWER,
                                 'Auto-reset on BUS-OFF': PCAN_BUSOFF_AUTORESET, 'CAN Listen-Only': PCAN_LISTEN_ONLY,
                                 'Debugs Log': PCAN_LOG_STATUS}

        self.m_FilteringRDB = 1

        self.m_USBValid_counter = 8 # number of valid messages to be read before validate the USB device sensed




    ## Initialize Unix Socket
    ##
    def InitializeSocket(self):
        if os.path.exists(os.path.join(SKT_PATH,SKT_PEAK)):
            os.remove(os.path.join(SKT_PATH,SKT_PEAK))

        print("Opening socket...{}".format(os.path.join(SKT_PATH,SKT_PEAK)))
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket_file = os.path.join(SKT_PATH,SKT_PEAK)
        self.server.bind(self.socket_file)

    ## Client - Server Acknoledge Unix Socket
    ##
    def AckSocket(self):
        print("Peak Socket waiting for client connection ...")
        self.server.listen(1)
        print('-> server listening for client ')
        self.conn, self.addr = self.server.accept()
        print('--> Sending answer to client')
        response = self.cbbChannel[-1].encode()
        self.conn.send(response)
        print("Sent {} over socket".format(response))


    ## Configures the Debug-Log file of PCAN-Basic
    ##
    def ConfigureLogFile(self):
        # Sets the mask to catch all events
        #
        iBuffer = LOG_FUNCTION_ALL

        # Configures the log file.
        # NOTE: The Log capability is to be used with the NONEBUS Handle. Other handle than this will
        # cause the function fail.
        #
        self.m_objPCANBasic.SetValue(PCAN_NONEBUS, PCAN_LOG_CONFIGURE, iBuffer)

    ## Configures the PCAN-Trace file for a PCAN-Basic Channel
    ##
    def ConfigureTraceFile(self):
        # Configure the maximum size of a trace file to 5 megabytes
        #
        iBuffer = 5
        stsResult = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_TRACE_SIZE, iBuffer)
        if stsResult != PCAN_ERROR_OK:
            self.IncludeTextMessage(self.GetFormatedError(stsResult))

        # Configure the way how trace files are created:
        # * Standard name is used
        # * Existing file is ovewritten,
        # * Only one file is created.
        # * Recording stopts when the file size reaches 5 megabytes.
        #
        iBuffer = TRACE_FILE_SINGLE | TRACE_FILE_OVERWRITE
        stsResult = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_TRACE_CONFIGURE, iBuffer)
        if stsResult != PCAN_ERROR_OK:
            self.IncludeTextMessage(self.GetFormatedError(stsResult))

    ## Help Function used to get an error as text
    ##
    def GetFormatedError(self, error):
        # Gets the text using the GetErrorText API function
        # If the function success, the translated error is returned. If it fails,
        # a text describing the current error is returned.
        #
        stsReturn = self.m_objPCANBasic.GetErrorText(error, 0)
        if stsReturn[0] != PCAN_ERROR_OK:
            return "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(error)
        else:
            return stsReturn[1]

    ## Includes a new line of text into the information Listview
    ##
    def IncludeTextMessage(self, strMsg):
        print(strMsg)


    ## Gets the current status of the PCAN-Basic message filter
    ##
    def GetFilterStatus(self):
        # Tries to get the sttaus of the filter for the current connected hardware
        #
        stsResult = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_MESSAGE_FILTER)

        # If it fails, a error message is shown
        #
        if stsResult[0] != PCAN_ERROR_OK:
            print("Error!", self.GetFormatedError(stsResult[0]))
            return False,
        else:
            return True, stsResult[1]

    ## Activates/deaactivates the different controls of the form according
    ## with the current connection status
    ##
    def SetConnectionStatus(self, bConnected=True):
        # Gets the status values for each case
        #
        self.btnGetVersions_Click()
        self.m_Connected = bConnected

    def FormatChannelName(self, handle, isFD=False):
        if handle < 0x100:
            devDevice = handle.value >> 4
            byChannel = handle.value & 0xF
        else:
            devDevice = handle.value >> 8
            byChannel = handle.value & 0xFF

        toRet = StringVar()
        if isFD:
            toRet.set('%s: FD %s (%.2X)' % (devDevice, byChannel, handle.value))
        else:
            toRet.set('%s: %s (%.2X)' % (devDevice, byChannel, handle.value))

        return toRet

    ################################################################################################################################################
    ### Message-proccessing functions
    ################################################################################################################################################
    def GetMsgString(self, msgStatus):
        # The Type of the message
        strTemp = msgStatus.TypeString
        toRet = (strTemp + " " * (self.m_ListColSpace[COL_TYPE] - len(strTemp)))
        # The msg ID
        strTemp = msgStatus.IdString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_ID] - len(strTemp)))
        # The length of the msg
        strTemp = str(GetLengthFromDLC(msgStatus.CANMsg.DLC, not (msgStatus.CANMsg.MSGTYPE & PCAN_MESSAGE_FD.value)))
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_LENGTH] - len(strTemp)))
        # The count of msgs
        strTemp = str(msgStatus.Count)
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_COUNT] - len(strTemp)))
        # The timestamp
        strTemp = msgStatus.TimeString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_TIME] - len(strTemp)))
        # The Data
        strTemp = msgStatus.DataString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_DATA] - len(strTemp)))

        return toRet

    ## Display CAN messages in the Message-ListView
    ##
    def DisplayMessages(self):
        with self._lock:
            for msgStatus in self.m_LastMsgsList:
                if not msgStatus.MarkedAsInserted:
                    self.lstMessages.insert(msgStatus.Position, text=self.GetMsgString(msgStatus))
                    msgStatus.MarkedAsInserted = True
                elif msgStatus.MarkedAsUpdated:
                    self.lstMessages.delete(msgStatus.Position)
                    self.lstMessages.insert(msgStatus.Position, text=self.GetMsgString(msgStatus))
                    msgStatus.MarkedAsUpdated = False

    ## Inserts a new entry for a new message in the Message-ListView
    ##
    def InsertMsgEntry(self, newMsg, timeStamp):
        # Format the new time information
        #
        with self._lock:
            # The status values associated with the new message are created
            #
            msgStsCurrentMsg = MessageStatus(newMsg, timeStamp, len(self.m_LastMsgsList))
            msgStsCurrentMsg.MarkedAsInserted = False
            msgStsCurrentMsg.ShowingPeriod = self.m_ShowPeriod
            self.m_LastMsgsList.append(msgStsCurrentMsg)

    def ProcessMessageFD(self, *args):
        with self._lock:
            # Split the arguments. [0] TPCANMsgFD, [1] TPCANTimestampFD
            #
            theMsg = args[0][0]
            itsTimeStamp = args[0][1]

            for msg in self.m_LastMsgsList:
                if (msg.CANMsg.ID == theMsg.ID) and (msg.CANMsg.MSGTYPE == theMsg.MSGTYPE):
                    msg.Update(theMsg, itsTimeStamp)
                    return
            self.InsertMsgEntry(theMsg, itsTimeStamp)

    ## Processes a received message, in order to show it in the Message-ListView
    ##
    def ProcessMessage(self, *args):
        with self._lock:
            # Split the arguments. [0] TPCANMsg, [1] TPCANTimestamp
            #
            theMsg = args[0][0]
            itsTimeStamp = args[0][1]

            newMsg = TPCANMsgFD()
            newMsg.ID = theMsg.ID
            newMsg.DLC = theMsg.LEN
            for i in range(8 if (theMsg.LEN > 8) else theMsg.LEN):
                newMsg.DATA[i] = theMsg.DATA[i]
            newMsg.MSGTYPE = theMsg.MSGTYPE
            newTimestamp = TPCANTimestampFD()
            newTimestamp.value = (
                        itsTimeStamp.micros + 1000 * itsTimeStamp.millis + 0x100000000 * 1000 * itsTimeStamp.millis_overflow)
            self.ProcessMessageFD([newMsg, newTimestamp])

    ## Thread-Function used for reading PCAN-Basic messages
    ##
    def CANReadThreadFunc(self):
        try:
            self.m_Terminated = False

            # Configures the Receive-Event.
            #
            stsResult = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_RECEIVE_EVENT, self.m_ReceiveEvent)

            if stsResult != PCAN_ERROR_OK:
                print("Error: " + self.GetFormatedError(stsResult))
            else:
                while not self.m_Terminated:
                    if win32event.WaitForSingleObject(self.m_ReceiveEvent, 50) == win32event.WAIT_OBJECT_0:
                        self.ReadMessages()

                # Resets the Event-handle configuration
                #
                self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_RECEIVE_EVENT, 0)
        except:
            print("Error occurred while processing CAN data")

        ################################################################################################################################################

    ### Event Handlers
    ################################################################################################################################################

    ## Form-Closing Function / Finish function
    ##
    def Form_OnClosing(self, event=None):
        # close current connection
        # if the event-thread is running the process would not terminate
        if (self.btnRelease['state'] != DISABLED):
            self.btnRelease_Click()
        # Releases the used PCAN-Basic channel
        #
        self.m_objPCANBasic.Uninitialize(self.m_PcanHandle)
        """Quit our mainloop."""
        self.exit = 0

    ## Button btnHwRefresh handler
    ##
    def btnHwRefresh_Click(self):

        # Clears the Channel comboBox and fill it again with
        # the PCAN-Basic handles for no-Plug&Play hardware and
        # the detected Plug&Play hardware
        #
        items = []
        # self.cbbChannel.subwidget('listbox').delete(0, Tix.END)

        try:
            # Python2
            iter_a_dict = self.m_CHANNELS.iteritems()
        except:
            # Python3
            iter_a_dict = self.m_CHANNELS.items()
        for name, value in iter_a_dict:
            # Includes all no-Plug&Play Handles
            #
            if (value.value <= PCAN_DNGBUS1.value):
                if False:
                    items.append(name)
            else:
                # Checks for a Plug&Play Handle and, according with the return value, includes it
                # into the list of available hardware channels.
                #
                result = self.m_objPCANBasic.GetValue(value, PCAN_CHANNEL_CONDITION)
                if (result[0] == PCAN_ERROR_OK) and (result[1] & PCAN_CHANNEL_AVAILABLE):
                    result = self.m_objPCANBasic.GetValue(value, PCAN_CHANNEL_FEATURES)
                    items.append(name)

        items.sort()
        self.cbbChannel = []
        for name in items:
            self.cbbChannel.insert(-1,name)
            print("Channel = {}".format(name))
        # self.cbbChannel['selection'] = self.cbbChannel.pick(Tix.END)

    ## Button btnInit handler
    ##
    def btnInit_Click(self):
        # gets the connection values
        #
        self.m_J1939BusFound = False

        for item in self.cbbChannel:

            self.m_PcanHandle = self.m_CHANNELS[item]
            baudrate = PCAN_BAUD_250K
            hwtype = PCAN_NONE
            ioport = PCAN_NONE
            interrupt = PCAN_NONE


            # Connects a selected PCAN-Basic channel
            #
            if self.m_IsFD:
                result = self.m_objPCANBasic.InitializeFD(self.m_PcanHandle, self.m_BitrateTXT.get())
            else:
                result = self.m_objPCANBasic.Initialize(self.m_PcanHandle, baudrate, hwtype, ioport, interrupt)

            if result != PCAN_ERROR_OK:
                if result != PCAN_ERROR_CAUTION:
                    print("Error!", self.GetFormatedError(result))
                else:
                    self.IncludeTextMessage('******************************************************')
                    self.IncludeTextMessage('The bitrate being used is different than the given one')
                    self.IncludeTextMessage('******************************************************')
                    result = PCAN_ERROR_OK
            else:
                # Prepares the PCAN-Basic's PCAN-Trace file
                #
                self.ConfigureTraceFile()

            # Sets the connection status of the form
            #
            self.SetConnectionStatus(result == PCAN_ERROR_OK)

            self.btnFilterApply_Click()

            stsResult = PCAN_ERROR_OK

            # We read at least one time the queue looking for messages.
            # If a message is found, we look again trying to find more.
            # If the queue is empty or an error occurr, we get out from
            # the dowhile statement.
            #
            counter= 0
            while (self.m_CanRead and not (stsResult & PCAN_ERROR_QRCVEMPTY) and counter <= self.m_USBValid_counter):
                result = self.m_objPCANBasic.Read(self.m_PcanHandle)
                stsResult = result[0]

                if stsResult == PCAN_ERROR_OK:
                    # We show the received message
                    #
                    msg = result[1]
                    print("Verify {} - read mxg {} on {} - OK - ID {} - data = [{} {} {} {} {} {} {} {}]".format(item,counter, self.m_USBValid_counter,
                                                                                        hex(msg.ID),
                                                                                        msg.DATA[0], msg.DATA[1],msg.DATA[2], msg.DATA[3],
                                                                                        msg.DATA[4], msg.DATA[5],msg.DATA[6], msg.DATA[7]  ))
                    counter += 1
                elif stsResult == PCAN_ERROR_QRCVEMPTY:
                    print("Empty readind queue - CAN BUS not connected to {}".format(item))


                    # stsResult = self.ReadMessageFD() if self.m_IsFD else self.ReadMessage()

                if stsResult == PCAN_ERROR_ILLOPERATION:
                    break

            if counter >= self.m_USBValid_counter:
                print("USB device {} ready! ".format(item))
                break



    ## Button btnRelease handler
    ##
    def btnRelease_Click(self):
        if WINDOWS_EVENT_SUPPORT:
            if self.m_ReadThread != None:
                self.m_Terminated = True
                self.m_ReadThread.join()
                self.m_ReadThread = None

        # We stop to read from the CAN queue
        #
        self.tmrRead.stop()

        # Releases a current connected PCAN-Basic channel
        #
        self.m_objPCANBasic.Uninitialize(self.m_PcanHandle)

        # Sets the connection status of the main-form
        #
        self.SetConnectionStatus(False)

    ## Button btnFilterApply handler
    ##
    def btnFilterApply_Click(self):
        if True:
            filterMode = PCAN_MODE_EXTENDED
        else:
            filterMode = PCAN_MODE_STANDARD

        # Gets the current status of the message filter
        #
        filterRet = self.GetFilterStatus()

        if not filterRet[0]:
            return


        # The filter will be full opened or complete closed
        #
        if self.m_FilteringRDB == 0:
            filterMode = PCAN_FILTER_CLOSE
            textEnd = "closed"
        else:
            filterMode = PCAN_FILTER_OPEN
            textEnd = "opened"

        # The filter is configured
        #
        result = self.m_objPCANBasic.SetValue(self.m_PcanHandle,
                                              PCAN_MESSAGE_FILTER,
                                              filterMode)

        # If success, an information message is written, if it is not, an error message is shown
        #
        if result == PCAN_ERROR_OK:
            self.IncludeTextMessage("The filter was successfully " + textEnd)
        else:
            tkMessageBox.showinfo("Error!", self.GetFormatedError(result))

    ## Button btnFilterQuery handler
    ##
    def btnFilterQuery_Click(self):
        # Queries the current status of the message filter
        #
        filterRet = self.GetFilterStatus()

        if filterRet[0]:
            if filterRet[1] == PCAN_FILTER_CLOSE:
                self.IncludeTextMessage("The Status of the filter is: closed.")
            elif filterRet[1] == PCAN_FILTER_OPEN:
                self.IncludeTextMessage("The Status of the filter is: full opened.")
            elif filterRet[1] == PCAN_FILTER_CUSTOM:
                self.IncludeTextMessage("The Status of the filter is: customized.")
            else:
                self.IncludeTextMessage("The Status ofself.tmrRead the filter is: Invalid.")

    ## Button btnParameterSet handler
    ##
    def btnParameterSet_Click(self):
        currentVal = self.cbbParameter['selection']
        iVal = self.m_PARAMETERS[currentVal]

        if self.m_ConfigurationRDB.get() == 1:
            iBuffer = PCAN_PARAMETER_ON
            lastStr = "activated"
            lastStr2 = "ON"
            lastStr3 = "enabled"
        else:
            iBuffer = PCAN_PARAMETER_OFF
            lastStr = "deactivated"
            lastStr2 = "OFF"
            lastStr3 = "disabled"

        # The Device-Number of an USB channel will be set
        #
        if iVal == PCAN_DEVICE_NUMBER:
            iBuffer = int(self.m_DeviceIdOrDelayNUD.get())
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_DEVICE_NUMBER, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The desired Device-Number was successfully configured")

        # The 5 Volt Power feature of a PC-card or USB will be set
        #
        elif iVal == PCAN_5VOLTS_POWER:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_5VOLTS_POWER, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The USB/PC-Card 5 power was successfully " + lastStr)

        # The feature for automatic reset on BUS-OFF will be set
        #
        elif iVal == PCAN_BUSOFF_AUTORESET:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_BUSOFF_AUTORESET, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The automatic-reset on BUS-OFF was successfully " + lastStr)

        # The CAN option "Listen Only" will be set
        #
        elif iVal == PCAN_LISTEN_ONLY:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_LISTEN_ONLY, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The CAN option ""Listen Only"" was successfully " + lastStr)

        # The feature for logging debug-information will be set
        #
        elif iVal == PCAN_LOG_STATUS:
            result = self.m_objPCANBasic.SetValue(PCAN_NONEBUS, PCAN_LOG_STATUS, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The feature for logging debug information was successfully " + lastStr)

        # The channel option "Receive Status" will be set
        #
        elif iVal == PCAN_RECEIVE_STATUS:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_RECEIVE_STATUS, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The channel option ""Receive Status"" was set to  " + lastStr2)

        # The feature for tracing will be set
        #
        elif iVal == PCAN_TRACE_STATUS:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_TRACE_STATUS, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The feature for tracing data was successfully " + lastStr)

        # The feature for tracing will be set
        #
        elif iVal == PCAN_CHANNEL_IDENTIFYING:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_CHANNEL_IDENTIFYING, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The procedure for channel identification was successfully " + lastStr)

        # The feature for using an already configured bit rate will be set
        #
        elif iVal == PCAN_BITRATE_ADAPTING:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_BITRATE_ADAPTING, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The feature for bit rate adaptation was successfully " + lastStr)

        # The option "Allow Status Frames" will be set
        #
        elif iVal == PCAN_ALLOW_STATUS_FRAMES:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_ALLOW_STATUS_FRAMES, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The reception of Status frames was successfully " + lastStr3)

        # The option "Allow RTR Frames" will be set
        #
        elif iVal == PCAN_ALLOW_RTR_FRAMES:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_ALLOW_RTR_FRAMES, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The reception of RTR frames was successfully " + lastStr3)

        # The option "Allow Error Frames" will be set
        #
        elif iVal == PCAN_ALLOW_ERROR_FRAMES:
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_ALLOW_ERROR_FRAMES, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The reception of Error frames was successfully " + lastStr3)

        # The option "Interframes Delay" will be set
        #
        elif iVal == PCAN_INTERFRAME_DELAY:
            iBuffer = int(self.m_DeviceIdOrDelayNUD.get())
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_INTERFRAME_DELAY, iBuffer)
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage("The delay between transmitting frames was successfully set")

                # The current parameter is invalid
        #
        else:
            result = (PCAN_ERROR_UNKNOWN, 0)
            tkMessageBox.showinfo("Error!", "Wrong parameter code.")

        # If the function fail, an error message is shown
        #
        if result != PCAN_ERROR_OK:
            tkMessageBox.showinfo("Error!", self.GetFormatedError(result))

    ## Button btnParameterGet handler
    ##
    def btnParameterGet_Click(self):
        currentVal = self.cbbParameter['selection']
        iVal = self.m_PARAMETERS[currentVal]

        # The Device-Number of an USB channel will be retrieved
        #
        if iVal == PCAN_DEVICE_NUMBER:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_DEVICE_NUMBER)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The configured Device-Number is {0:X}h".format(result[1]))

        # The activation status of the 5 Volt Power feature of a PC-card or USB will be retrieved
        #
        elif iVal == PCAN_5VOLTS_POWER:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_5VOLTS_POWER)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The 5-Volt Power of the USB/PC-Card is " + lastStr)

        # The activation status of the feature for automatic reset on BUS-OFF will be retrieved
        #
        elif iVal == PCAN_BUSOFF_AUTORESET:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_BUSOFF_AUTORESET)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The automatic-reset on BUS-OFF is " + lastStr)

        # The activation status of the CAN option "Listen Only" will be retrieved
        #
        elif iVal == PCAN_LISTEN_ONLY:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_LISTEN_ONLY)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The CAN option ""Listen Only"" is " + lastStr)

        # The activation status for the feature for logging debug-information will be retrieved
        #
        elif iVal == PCAN_LOG_STATUS:
            result = self.m_objPCANBasic.GetValue(PCAN_NONEBUS, PCAN_LOG_STATUS)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The feature for logging debug information is " + lastStr)

        # The activation status of the channel option "Receive Status"  will be retrieved
        #
        elif iVal == PCAN_RECEIVE_STATUS:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_RECEIVE_STATUS)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The channel option ""Receive Status"" is " + lastStr)

        # The Number of the CAN-Controller used by a PCAN-Channel
        #
        elif iVal == PCAN_CONTROLLER_NUMBER:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_CONTROLLER_NUMBER)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The CAN Controller number is {0}".format(result[1]))

        # The activation status for the feature for tracing data will be retrieved
        #
        elif iVal == PCAN_TRACE_STATUS:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_TRACE_STATUS)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The feature for tracing data is " + lastStr)

        # The activation status of the Channel Identifying procedure will be retrieved
        #
        elif iVal == PCAN_CHANNEL_IDENTIFYING:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_CHANNEL_IDENTIFYING)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The identification procedure of the selected channel is " + lastStr)

        # The extra capabilities of a hardware will asked
        #
        elif iVal == PCAN_CHANNEL_FEATURES:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_CHANNEL_FEATURES)
            if result[0] == PCAN_ERROR_OK:
                if (result[1] & FEATURE_FD_CAPABLE) == FEATURE_FD_CAPABLE:
                    lastStr = "does support"
                else:
                    lastStr = "DOESN'T SUPPORT"
                self.IncludeTextMessage("The channel %s Flexible Data-Rate (CAN-FD) " % lastStr)
                if (result[1] & FEATURE_DELAY_CAPABLE) == FEATURE_DELAY_CAPABLE:
                    lastStr = "does support"
                else:
                    lastStr = "DOESN'T SUPPORT"
                self.IncludeTextMessage("The channel %s an inter-frame delay for sending messages " % lastStr)

                # The status of the bit rate adapting feature will be retrieved
        #
        elif iVal == PCAN_BITRATE_ADAPTING:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_BITRATE_ADAPTING)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The feature for bit rate adaptation is %s" % lastStr)

        # The bit rate of the connected channel will be retrieved (BTR0-BTR1 value)
        #
        elif iVal == PCAN_BITRATE_INFO:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_BITRATE_INFO)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The bit rate of the channel is %.4Xh" % result[1])

        # The bit rate of the connected FD channel will be retrieved (String value)
        #
        elif iVal == PCAN_BITRATE_INFO_FD:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_BITRATE_INFO_FD)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The bit rate of the channel is %s" % result[1])

        # The nominal speed configured on the CAN bus will be retrived (bits/second)
        #
        elif iVal == PCAN_BUSSPEED_NOMINAL:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_BUSSPEED_NOMINAL)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The nominal speed of the channel is %d bit/s" % result[1])

        # The data speed configured on the CAN bus will be retrived (bits/second)
        #
        elif iVal == PCAN_BUSSPEED_DATA:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_BUSSPEED_DATA)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The data speed of the channel is %d bit/s" % result[1])

        # The IP address of a LAN channel as string, in IPv4 format
        #
        elif iVal == PCAN_IP_ADDRESS:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_IP_ADDRESS)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The IP address of the channel is %s" % result[1])

                # The running status of the LAN Service
        #
        elif iVal == PCAN_LAN_SERVICE_STATUS:
            result = self.m_objPCANBasic.GetValue(PCAN_NONEBUS, PCAN_LAN_SERVICE_STATUS)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == SERVICE_STATUS_RUNNING:
                    lastStr = "running"
                else:
                    lastStr = "NOT running"
                self.IncludeTextMessage("The LAN service is %s" % lastStr)

        # The reception of Status frames
        #
        elif iVal == PCAN_ALLOW_STATUS_FRAMES:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_ALLOW_STATUS_FRAMES)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "enabled"
                else:
                    lastStr = "disabled"
                self.IncludeTextMessage("The reception of Status frames is %s" % lastStr)

        # The reception of RTR frames
        #
        elif iVal == PCAN_ALLOW_RTR_FRAMES:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_ALLOW_RTR_FRAMES)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "enabled"
                else:
                    lastStr = "disabled"
                self.IncludeTextMessage("The reception of RTR frames is %s" % lastStr)

        # The reception of Error frames
        #
        elif iVal == PCAN_ALLOW_ERROR_FRAMES:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_ALLOW_ERROR_FRAMES)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "enabled"
                else:
                    lastStr = "disabled"
                self.IncludeTextMessage("The reception of Error frames is %s" % lastStr)

        # The Interframe delay of an USB channel will be retrieved
        #
        elif iVal == PCAN_INTERFRAME_DELAY:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_INTERFRAME_DELAY)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The configured interframe delay is {0} ms".format(result[1]))

                # The current parameter is invalid
        #
        else:
            result = (PCAN_ERROR_UNKNOWN, 0)
            tkMessageBox.showinfo("Error!", "Wrong parameter code.")

        # If the function fail, an error message is shown
        #
        if result[0] != PCAN_ERROR_OK:
            tkMessageBox.showinfo("Error!", self.GetFormatedError(result[0]))

    ## Function for reading CAN messages on normal CAN devices
    ##
    def ReadMessage(self):
        # We execute the "Read" function of the PCANBasic
        #
        result = self.m_objPCANBasic.Read(self.m_PcanHandle)

        if result[0] == PCAN_ERROR_OK:
            # We show the received message
            #
            self.ProcessMessage(result[1:])

        return result[0]

    def ReadMessageFD(self):
        # We execute the "ReadFD" function of the PCANBasic
        #
        result = self.m_objPCANBasic.ReadFD(self.m_PcanHandle)

        if result[0] == PCAN_ERROR_OK:
            # We show the received message
            #
            self.ProcessMessageFD(result[1:])

        return result[0]

    def ReadMessages(self):
        stsResult = PCAN_ERROR_OK

        # We read at least one time the queue looking for messages.
        # If a message is found, we look again trying to find more.
        # If the queue is empty or an error occurr, we get out from
        # the dowhile statement.
        #
        while (self.m_CanRead and not (stsResult & PCAN_ERROR_QRCVEMPTY)):
            stsResult = self.ReadMessageFD() if self.m_IsFD else self.ReadMessage()
            if stsResult == PCAN_ERROR_ILLOPERATION:
                break

    ## Button btnRead handler
    ##
    def btnRead_Click(self):
        # We execute the "Read" function of the PCANBasic
        #
        result = self.ReadMessageFD() if self.m_IsFD else self.ReadMessage()
        if result != PCAN_ERROR_OK:
            # If an error occurred, an information message is included
            #
            self.IncludeTextMessage(self.GetFormatedError(result))

    ## Button btnGetVersions handler
    ##
    def btnGetVersions_Click(self):
        # We get the vesion of the PCAN-Basic API
        #
        result = self.m_objPCANBasic.GetValue(PCAN_NONEBUS, PCAN_API_VERSION)
        if result[0] == PCAN_ERROR_OK:
            print("API Version: {}".format(result[1]))
            # We get the driver version of the channel being used
            #
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_CHANNEL_VERSION)
            if result[0] == PCAN_ERROR_OK:
                # Because this information contains line control characters (several lines)
                # we split this also in several entries in the Information List-Box
                #
                lines_str = "{}".format(result[1]).split('\n')

                print("Channel/Driver Version: ")
                for line in lines_str:
                    line = line.encode()
                    print("     * {}".format(line))

        # If an error ccurred, a message is shown
        #
        if result[0] != PCAN_ERROR_OK:
            print("Error!", self.GetFormatedError(result[0]))


    ## Button btnReset handler
    ##
    def btnReset_Click(self):
        # Resets the receive and transmit queues of a PCAN Channel.
        #
        result = self.m_objPCANBasic.Reset(self.m_PcanHandle)

        # If it fails, a error message is shown
        #
        if result != PCAN_ERROR_OK:
            print("Error!", self.GetFormatedTex(result))
        # else:
        #     print("Receive and transmit queues successfully reset")
        #     pass

    ## Button btnStatus handler
    ##
    def btnStatus_Click(self):
        # Gets the current BUS status of a PCAN Channel.
        #
        result = self.m_objPCANBasic.GetStatus(self.m_PcanHandle)

        # Switch On Error Name
        #
        if result == PCAN_ERROR_INITIALIZE:
            errorName = "PCAN_ERROR_INITIALIZE"
        elif result == PCAN_ERROR_BUSLIGHT:
            errorName = "PCAN_ERROR_BUSLIGHT"
        elif result == PCAN_ERROR_BUSHEAVY:  # PCAN_ERROR_BUSWARNING
            errorName = "PCAN_ERROR_BUSHEAVY" if not self.m_IsFD else "PCAN_ERROR_WARNING"
        elif result == PCAN_ERROR_BUSPASSIVE:
            errorName = "PCAN_ERROR_BUSPASSIVE"
        elif result == PCAN_ERROR_BUSOFF:
            errorName = "PCAN_ERROR_BUSOFF"
        elif result == PCAN_ERROR_OK:
            errorName = "PCAN_ERROR_OK"
        else:
            errorName = "See Documentation"

        # Display Message
        #
        self.IncludeTextMessage("Status: {0} ({1:X}h)".format(errorName, result))


###*****************************************************************

if __name__ == '__main__':
    global basicExl
    root = "root"
    # Creates a PCAN-Basic application
    #
    basicExl = PCANBasicExample()

    # Runs the Application / loop-start
    #
    basicExl.loop()

    # Application's destrution / loop-end
    #
    basicExl.destroy()


###*****************************************************************