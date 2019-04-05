import os
import datetime
import time
import usb.util
import sys
import  subprocess
from subprocess import Popen, PIPE
import curses
import hashlib
from shutil import copyfile


def hash_file(filename):
    """"This function returns the SHA-1 hash
    of the file passed into it"""

    # make a hash object
    h = hashlib.sha1()

    # open file for reading in binary mode
    with open(filename,'rb') as file:

        # loop till the end of the file
        chunk = 0
        while chunk != b'':
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()


def get_size(start_path = '.'):
    total_size = 0
    total_file = 0
    file_list =  []
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            file_pointer = os.path.join(dirpath, f)
            total_size += os.path.getsize(file_pointer)
            total_file += 1
            file_list.append(file_pointer)
    return total_file, total_size, file_list


def DisplayBackupStatus(stdscr, root_path, data_path):

    dir_name_suffix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dir_name = "DATALOG_BACKUP" + dir_name_suffix
    dir_path = os.path.join(root_path, dir_name)
    del dir_name_suffix

    # Clear and refresh the screen for a blank canvas

    stdscr.nodelay(True)
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLUE)
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_YELLOW)

    # Initialization
    stdscr.clear()
    height, width = stdscr.getmaxyx()


    title = "METATRON - TECHNOLOGY1604 - NATURAL GAS APPLICATION DATALOG"[:width - 1]
    subtitle = "Written by Giuseppe Miletto - Metatron "[:width - 1]
    # Centering calculations

    # Turning on attributes for title
    stdscr.attron(curses.color_pair(2))
    stdscr.attron(curses.A_BOLD)

    # Rendering title
    stdscr.addstr(0, 0, title)

    # Turning off attributes for title
    stdscr.attroff(curses.color_pair(2))
    stdscr.attroff(curses.A_BOLD)

    # Refresh the screen
    stdscr.refresh()

    statvfs = os.statvfs(root_path)

    total_space = statvfs.f_frsize * statvfs.f_blocks
    row = "  # Size of backup device's filesystem in bytes = {}".format(total_space)
    stdscr.addstr(2, 2, row)

    free_space = statvfs.f_frsize * statvfs.f_bfree
    row = "  # Free bytes = {} ;  free percentage = {}%".format(free_space,int(free_space/total_space*100))  # Actual number of free bytes
    stdscr.addstr(3, 2, row)

    number_data_file, data_total_size , file_list = get_size(data_path)
    if number_data_file < 1:
        row = "No data file found in {} - NOTHING TO DO! Exit!".format(data_path)
        # Turning on attributes
        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)
        # Adding an important row
        stdscr.addstr(4, 2, row)
        # Turning off attributes
        stdscr.attroff(curses.color_pair(2))
        stdscr.attroff(curses.A_BOLD)
        stdscr.refresh()

        sys.exit(0)
    else:
        row = "  # DATA dir =  {} | Number of datafile = {}  | Total size = {}".format(data_path, number_data_file, data_total_size)  # Actual number of free bytes
        # Turning on attributes
        stdscr.attron(curses.color_pair(4))
        stdscr.attron(curses.A_BOLD)
        # Adding an important row
        stdscr.addstr(4, 2, row)
        # Turning off attributes
        stdscr.attroff(curses.color_pair(4))
        stdscr.attroff(curses.A_BOLD)

        if data_total_size <= free_space:
            row = "Verified space OK. Starting backup - Adding the folder '{}'".format(dir_name)
            # Turning on attributes
            stdscr.attron(curses.color_pair(4))
            stdscr.attron(curses.A_BOLD)
            # Adding an important row
            stdscr.addstr(5, 2, row)
            # Turning off attributes
            stdscr.attroff(curses.color_pair(4))
            stdscr.attroff(curses.A_BOLD)

            os.makedirs(dir_path)
        else:
            if data_total_size > total_space:
                row = "NOT ENOUGH SPACE FOR BACKUP! USB Media size too small - please use a bigger one! Exit!"
            else:
                row = "NOT ENOUGH SPACE FOR BACKUP! Please free USB Media space or replace with a bigger one! Exit!"
            # Turning on attributes
            stdscr.attron(curses.color_pair(2))
            stdscr.attron(curses.A_BOLD)
            # Adding an important row
            stdscr.addstr(5, 2, row)
            # Turning off attributes
            stdscr.attroff(curses.color_pair(2))
            stdscr.attroff(curses.A_BOLD)
            stdscr.refresh()
            sys.exit(0)

    # Turning on attributes
    stdscr.attron(curses.color_pair(3))
    stdscr.attron(curses.A_BOLD)
    # Adding an important row
    row = "MOVING FILES FROM {}".format(data_path)
    row += " " * (width - len(row) - 2)
    stdscr.addstr(7, 0, row)
    row = "               TO {}".format(dir_path)
    row += " " * (width - len(row) - 2)
    stdscr.addstr(8, 0, row)
    # Turning off attributes
    stdscr.attroff(curses.color_pair(3))
    stdscr.attroff(curses.A_BOLD)

    stdscr.refresh()

    for idx, source_file_path in enumerate(file_list):
        hpos = 11
        # Turning on attributes
        stdscr.attron(curses.color_pair(5))
        stdscr.attron(curses.A_BOLD)
        row = "SOURCE  {: >3} of {: >3} :".format(idx+1, number_data_file)
        row += " " * (width - len(row) - 2)
        stdscr.addstr(hpos, 0, row)
        stdscr.refresh()
        stdscr.attroff(curses.A_BOLD)

        hpos = 12
        filename = source_file_path.split('/')[-1]
        row = "{: <36}- SHA1:".format(filename)
        row += " " * (width - len(row) - 2)
        stdscr.addstr(hpos, 0, row)
        stdscr.refresh()
        source_sha1 = hash_file(source_file_path)
        row = "{: <36}- SHA1: {:<}".format(filename, source_sha1)
        row += " " * (width - len(row) - 2)
        stdscr.addstr(hpos, 0, row)
        stdscr.refresh()
        time.sleep(0.25)


        stdscr.attroff(curses.color_pair(5))
        stdscr.attron(curses.color_pair(6))
        stdscr.attron(curses.A_BOLD)
        hpos = 14
        target_file_path = os.path.join(dir_path, filename)
        row = "Destination : {}".format(target_file_path)
        row += " " * (width - len(row) - 2)
        stdscr.addstr(hpos, 0, row)
        stdscr.refresh()
        stdscr.attroff(curses.A_BOLD)

        hpos = 15
        try:
            copyfile(source_file_path, target_file_path)
            row = "{: <36}- SHA1:".format(target_file_path.split('/')[-1])
            row += " " * (width - len(row) - 2)
            stdscr.addstr(hpos, 0, row)
            stdscr.refresh()
        except:
            pass
        target_sha1 = hash_file(target_file_path)
        row = "{: <36}- SHA1: {:<}".format(target_file_path.split('/')[-1], target_sha1)
        row += " " * (width - len(row) - 2)
        stdscr.addstr(hpos, 0, row)
        stdscr.refresh()
        time.sleep(0.5)

        hpos = 17
        stdscr.attroff(curses.color_pair(6))
        if source_sha1 == target_sha1:
            stdscr.attron(curses.color_pair(4))
            row = "HASH VERIFIED OK. REMOVING SOURCE {: <36}".format(filename, target_sha1)
            row += " " * (width - len(row) - 2)
            stdscr.addstr(hpos, 0, row)
            stdscr.refresh()
            stdscr.attroff(curses.color_pair(4))
            try:
                os.remove(source_file_path)
            except OSError as e:
                stdscr.attron(curses.color_pair(2))
                hpos=18
                row = "Error '{}' while removing source file {}".format(e,filename)
                row += " " * (width - len(row) - 2)
                stdscr.addstr(hpos, 0, row)
                stdscr.refresh()
                stdscr.attroff(curses.color_pair(2))
                time.sleep(5)

        else:
            stdscr.attron(curses.color_pair(2))
            row = "HASH VERIFIED KO. NOT REMOVING SOURCE {: <36}".format(filename, target_sha1)
            row += " " * (width - len(row) - 2)
            stdscr.addstr(hpos, 0, row)
            stdscr.refresh()
            stdscr.attroff(curses.color_pair(2))
            time.sleep(2.25)

        time.sleep(0.75)

        row= " "*(width-1)
        for hpos in range(10,19):
            stdscr.addstr(hpos, 0, row)
        stdscr.refresh()


if __name__ == "__main__":
    usb_stick_found = False
    data_path = "/home/pi/DATA"
    # find device
    devs = usb.core.find(find_all=True)
    dev_name = "sda1"
    mountpoint= "/media/usb1"
    # for dev in devs:
    #     for cfg in dev:
    #         for intf in cfg:
    #             #			print 'Bus %03x,Device %03x | %04x:%04x - (%d) ... bDeviceClass %02x , bInterfaceClass %02x' % (dev.bus, dev.address, dev.idVendor, dev.idProduct, dev.bNumConfigurations, dev.bDeviceClass, intf.bInterfaceClass)
    #             if dev.bDeviceClass == 0 and intf.bInterfaceClass == 8:
    #                 print('Bus %03x,Device %03x | %04x:%04x' % (dev.bus, dev.address, dev.idVendor, dev.idProduct))
    #                 usb_stick_found = True
    #                 break

    try:
        with Popen("ls /dev/sd*", shell=True, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
            for line in p.stdout:
                if "sda" in line:
                    usb_stick_found = True
                    dev_name = "sda1"
                elif "sdb" in line:
                    usb_stick_found = True
                    dev_name = "sdb1"
                elif "sdc" in line:
                    usb_stick_found = True
                    dev_name = "sdc1"
                elif "sdd" in line:
                    usb_stick_found = True
                    dev_name = "sdd1"

    except:
        print("USB key not found. Backup procedure not started")
        sys.exit(0)


    if usb_stick_found:
        print("A USB device has been detected. Starting the backup procedure")
        rv3 = subprocess.call("mountpoint -q /mnt/{}/".format(dev_name), shell=True)
        print(rv3)
        if rv3:
            print("Mounting USB stick detected as device /dev/{} in {} ".format(dev_name, mountpoint))
            subprocess.call("sudo mount /dev/{} {} -o uid=pi,gid=pi".format(dev_name, mountpoint), shell=True)
        else:
            print("USB stick detected as device {} already mounted in {} ".format(dev_name, mountpoint))

        try:
            fp = open(os.path.join(mountpoint,"writetest.test"),"wb")
            fp.write(b"test a line \n")
            fp.close()
            os.remove(os.path.join(mountpoint,"writetest.test"))
            print("Writing access verified in {}".format(os.path.join(mountpoint,"writetest.test")))
        except:
            print("Problem for writing in {}".format(os.path.join(mountpoint,"writetest.test")))
            sys.exit(1)

    else:
        sys.exit(0)

    # Inside curses wrapper the complete procedure
    curses.wrapper(DisplayBackupStatus, mountpoint, data_path)
    sys.exit(0)