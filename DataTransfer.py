#!/usr/bin/env python3
"""
Bostin Technology  (see www.CognIoT.eu)

Provides the overall functionality to transfer data from one device to another.
Currently set to use LoRa Comms as no other communications available

Command Line Options
    - Operate as a Hub (default action)             -u --hub
    - Operate as a Node                             -n --node
    - Display Customer Parameters                   -o --displayinfo
    - Set Customer Parameters                       -a --setinfo

Operational Info (op_info)
['dir_read_freq'] - The frequency of directory reading
['hub_addr'] - The address of the Hub
['node_addr'] - The address of the Node

Future upgrade is to have more parameters and allow the user to select directories etc.
"""

import sys
import Standard_Settings as SS
import json
import os
import logging
import logging.config
import dict_LoggingSetup
import argparse
from datetime import datetime
from datetime import timedelta
import time

from LoRaCommsReceiverV2 import LoRaComms as LoRa
from cls_CognIoTRF import Node
from cls_CognIoTRF import Hub




def SetandGetArguments():
    """
    Define the arguments available for the program and return any arguments set.

    """

    gbl_log.info("[CTRL] Setting and Getting Parser arguments")
    parser = argparse.ArgumentParser(description="Set the functionality for transferring data using LoRa")
    Main_group = parser.add_mutually_exclusive_group()
    Main_group.add_argument("-u", "--hub", action="store_true",
                    help="Run as a Hub, receiving and storing data")
    Main_group.add_argument("-n", "--node", action="store_true",
                    help="Run as a Node, sending already stored data")
    Para_group = parser.add_mutually_exclusive_group()
    Para_group.add_argument("-d", "--displayinfo", action="store_true",
                    help="Display the Configuration Information, e.g. Read or Write directory")
    Para_group.add_argument("-s", "--setinfo", action="store_true",
                    help="Set the Configuration parameters, e.g.Read Frequency")
    gbl_log.debug("[CTRL] Parser values captured: %s" % parser.parse_args())
    return parser.parse_args()

def SetupLogging():
    """
    Setup the logging defaults
    Using the logger function to span multiple files.
    """
    global gbl_log
    # Create a logger with the name of the function
    logging.config.dictConfig(dict_LoggingSetup.log_cfg)
    gbl_log = logging.getLogger()

    gbl_log.info("\n\n")
    gbl_log.info("[CTRL] Logging Started, current level is %s" % gbl_log.getEffectiveLevel())

    return

def DisplayOperationalParameters(op_info):
    """
    Perform the necessary actions to display the operational information being used

    """
    print("Setting                  Value")
    print("==============================")
    for item in op_info:
        print("%s%s" %( '{0: <25}'.format(item), op_info[item]))

    return

def SetOperationalParameters():
    """
    Perform the necessary actions to allow the clinet to set the parameter data being used

    Parameters to be captured
    - Directory Read Frequency (dir_read_freq)
    - Node Address with default (hub_addr)
    - Hub Address with default (node_addr)

    """

    print("Setting Operational Information\n")
    op_info = {}

    choice = ""
    while choice == "":
        choice = input("Please enter the Directory Read Frequency (1 - 100) seconds?")
        if choice.isdigit():
            choice = int(choice)
            if choice in range(1,100):
                op_info['dir_read_freq'] = choice
        else:
            print("Please enter a number in the range 1 to 100")
            choice = ""
    gbl_log.debug("[CTRL] Directory Read Frequency Number:%s" % choice)

    choice = ""
    while choice == "":
        choice = input("Please enter the Hub Address (4chr Hex)? ")
        if len(choice) == 4:
            op_info['hub_addr'] = choice
        else:
            print("Please enter a number")
            choice = ""
    gbl_log.debug("[CTRL] Hub Address:%s" % choice)

    choice = ""
    while choice == "":
        choice = input("Please enter the Node Address (4chr Hex)? ")
        if len(choice) == 4:
            op_info['node_addr'] = choice
        else:
            print("Please enter a number")
            choice = ""
    gbl_log.debug("[CTRL] Node Address:%s" % choice)
    
    #TODO: Add in setting of the sensor info at this stage?

    SaveOperationalInfo(op_info)

    return op_info

def SplashScreen():
    print("***********************************************")
    print("*             Bostin Technology               *")
    print("*                                             *")
    print("*             Mobile IoT Sensor               *")
    print("*                                             *")
    print("*        for more info www.cognIoT.eu         *")
    print("***********************************************\n")
    return

def LoadOperationalInfo():
    """
    Load the Operational File information and return it in a dictionary
    op_info = {"dir_read_freq": nnn}

    """
    opfile = {}
    gbl_log.info("[CTRL] Reading the operational file information")
    filename = SS.OPFILE_LOCATION + '/' + SS.OPFILE_NAME
    if os.path.isfile(filename):
        gbl_log.debug("[CTRL] Operational File in location:%s" % filename)
        with open(filename, mode='r') as op:
            opfile = json.load(op)

    else:
        print("No existing operational file, please Set Operational info")
        gbl_log.info("[CTRL] No Operational file exisitng")

    # Validate the operational info that has been read back.
    status = True
    for item in ['dir_read_freq', 'hub_addr', 'node_addr']:
        if item not in opfile:
            status = False
            gbl_log.info("[CTRL] Missing item from the operational file:%s" % item)

    gbl_log.debug("[CTRL] Operational data being returned:%s" % opfile)
    return status, opfile

def SaveOperationalInfo(op_info):
    """
    Take the op_info and write it to the file
    Disk management is handled as part of the Control module
    """

    gbl_log.debug("[CTRL] Data being written to the operational file:%s" % op_info)
    with open(SS.OPFILE_LOCATION + '/' + SS.OPFILE_NAME, mode='w') as f:
        json.dump(op_info, f)
        gbl_log.info("[CTRL] Operational File updated")

    return

def WriteDataToDir(dataset):
    """
    Write the given data to the operational directory
    Takes the given data and creates a new file with the contents of it
    Format of the filename is based on standard settings
        RECORDFILE_NAME+timestamp+RECORDFILE_EXT
    Stored in sub folder
        RECORDFILE_LOCATION
    Returns true if the record is written, or false if it isn't
    Disk space management is handled by the calling program
    """
    status = False
    file_time = datetime.now().strftime("%y%m%d%H%M%S-%f")

    #TODO: If the datafile directoryu doesn't exist, an error is thrown!

    data_record_name = SS.RECORDFILE_LOCATION + '/' + SS.RECORDFILE_NAME + file_time + SS.RECORDFILE_EXT
    gbl_log.info("[DAcc] Writing new record to disk:%s" % data_record_name)

    #TODO: Need to handle a failure to open the file
    with open(data_record_name, mode='w') as f:
        #json.dump(dataset, f)
        f.write(dataset.decode('utf-8'))        # Debug TEst
        status = True
    return status

    return

def Hub_Loop(op_info):
    """
    Perform the necessary functionality to operate as a Hub
    """
    gbl_log.info("[CTRL] Starting Hub Operation")
    try:
        comms = LoRa()
        decode = Hub(op_info['hub_addr'], op_info['node_addr'])
        while True:
            message = comms.receive()
            print("\r\r\r\r\r\r\rWaiting", end="")
            gbl_log.debug("[CTRL] Message received from the comms:%s" % message)
            decode.decode_and_respond(message)
            if decode.reply_status:
                print("\r\r\r\r\r\r\rReading", end="")
                if decode.reply_payload_len() > 0:
                    WriteDataToDir(decode.reply_payload())
                status = comms.transmit(decode.reply())
                #TODO: Add some capability to retry if failure

    except KeyboardInterrupt:
        # CTRL - C entered
        print(" CTRL-C entered")
        gbl_log.debug("[CTRL] User Interrupt occurred (Ctrl-C)")
        gbl_log.info("[CTRL] End of Processing")

        #TODO: Need to add in some functionality here to stop the sensor.
    except:
        #Error occurrred
        gbl_log.critical("[CTRL] Error occurred whilst looping to read values")
        print("\nCRITICAL ERROR during rading of sensor values- contact Support\n")
        gbl_log.exception("[CTRL] Start reading loop Exception Data")
    return

def ValidateRecord(contents):
    """
    Check the contents of the record open are valid and contain the right information
    If the record is good, return True, else return False
    """
    status = True
    if len(contents) < SS.RECORDFILE_MIN_SIZE or len(contents) > SS.RECORDFILE_MAX_SIZE:
        status = False
    #TODO: Add other checks for validation
    return status

def GetRecord():
    """
    Get a file from the directory and return its name and the contents of it

    If there isn't any record, return an empty list
    """

    gbl_log.info("[CTRL] Getting the list of files to use and selecting one")
    record = ''
    list_of_files = os.listdir(path=SS.RECORDFILE_LOCATION+'/.')
    if len(list_of_files) > 0:
        list_of_files.sort()
        gbl_log.debug("[CTRL] Files to Use :%s" % list_of_files)
        # Check for files before returning one
        for record_to_use in list_of_files:
            gbl_log.debug("[CTRL] File being checked for extension of %s:%s" % (SS.RECORDFILE_EXT, record_to_use))
            if record_to_use.endswith(SS.RECORDFILE_EXT):
                gbl_log.debug("[CTRL] Record Selected for use:%s" % record_to_use)

                with open(SS.RECORDFILE_LOCATION+'/'+record_to_use, mode='r') as f:
                    #record = json.load(f)
                    record=f.read()        #TEST
                    gbl_log.debug("[CTRL] Record loaded for use:%s" % record)
                if ValidateRecord(record):
                    # The record is good and therefore I need to exit
                    break
                else:
                    # The file is not valid and therefore is moved to the archive list
                    RenameRecordFile(record_to_use)
    return (record_to_use, record)

def RemoveRecordFile(record_to_remove):
    """
    Remove the file from the directory
    """

    if os.path.isfile(SS.RECORDFILE_LOCATION+'/' + record_to_remove):
        os.remove(SS.RECORDFILE_LOCATION+'/' + record_to_remove)
        gbl_log.info("[CTRL] Record File deleted:%s" % SS.RECORDFILE_LOCATION+'/' + record_to_remove)
    else:
        gbl_log.info("[CTRL] Record file not found:%s" % SS.RECORDFILE_LOCATION+'/' + record_to_remove)
    return

def RenameRecordFile(record_to_rename):
    """
    Rename the current file to the old name so it is no longer sent
    """
    if os.path.isfile(SS.RECORDFILE_LOCATION+'/' + record_to_rename):
        os.rename(SS.RECORDFILE_LOCATION+'/' + record_to_rename, SS.RECORDFILE_LOCATION+'/' + record_to_rename[-3:] + SS.RECORDFILE_OLD)
        gbl_log.info("[DAcc] Record File renamed:%s" % SS.RECORDFILE_LOCATION+'/' + record_to_rename[-3:] + SS.RECORDFILE_OLD)
    else:
        gbl_log.info("[DAcc] Record File NOT renamed:%s" % SS.RECORDFILE_LOCATION+'/' + record_to_rename[-3:] + SS.RECORDFILE_OLD)
    return
    
def Node_Loop_old(op_info):
    """
    Perform the necessary functions to act as a node.
    """
    gbl_log.info("[CTRL] Starting Node Operation")
    try:
        comms = LoRa()
        sender = Node(op_info['hub_addr'], op_info['node_addr'])
        retries = SS.RETRIES
        while True:
            # Start the timer
            endtime = datetime.now() + timedelta(seconds=op_info['dir_read_freq'])
            print("\r\r\r\r\r\r\rReading", end="")

            # Loop round to get data and send it

            record_name, data_record = GetRecord()
            gbl_log.info("[CTRL] Record to send >%s< and its contents:%s" % ( record_name, data_record))
            if len(data_record) > 0:
                data_to_send = True
                while data_to_send:
                    # pass in the data
                    sender.data_to_be_sent(data_record)
                    # get the message to send
                    message = sender.message_to_send()
                    gbl_log.info("[CTRL] Message To Send:%s" % message)
                    # send the message
                    status = comms.transmit(message)
                    gbl_log.info("[CTRL] Message Send Status:%s" % status)
                    # get and check the response
                    reply = comms.receivetimeout(SS.REPLY_WAIT)
                    gbl_log.info("[CTRL] Message Reply:%s" % reply)
                    status = sender.check_response(reply)
                    gbl_log.info("[CTRL] Message Reply Status:%s" % status)
                    if status == True:
                        # if good, remove the record
                        RemoveRecordFile(record_name)
                        retries = SS.RETRIES
                        # check for more data
                        record_name, data_record = GetRecord()
                        if len(data_record) > 0:
                            data_to_send = True
                        else:
                            data_to_send = False
                    else:
                        # else drop out but increase the retries count.
                        gbl_log.debug("[CTRL] Response status is negative, checking fo retry count")
                        retries = retries - 1
                        if retries == 0:
                            # Stop attempting to send the file and break out of the overall loop
                            data_to_send = False
                        else:
                            time.sleep(retries)        # Wait for a period before retrying

            else:
                # get the message to send
                message = sender.message_to_send
                # send the message
                status = comms.transmit(message)
                # check the response
                if status == True:
                    retries = SS.RETRIES
                else:
                    retires = retries - 1
                
            # Wait for timeout
            waiting = False
            while endtime > datetime.now():
                if waiting == False:
                    print("\r\r\r\r\r\r\rWaiting", end="")
                    gbl_log.debug("[CTRL] Waiting for timeout to complete")
                    waiting=True
                # Use time.sleep to wait without processor burn at 25%
                sleep = datetime.now() - endtime
                if sleep.total_seconds() > 2:
                    time.sleep(sleep.total_seconds() - 0.1)
                else:
                    time.sleep(0.1)
        
    except KeyboardInterrupt:
        # CTRL - C entered
        print(" CTRL-C entered")
        gbl_log.debug("[CTRL] User Interrupt occurred (Ctrl-C)")
        gbl_log.info("[CTRL] End of Processing")

        #TODO: Need to add in some functionality here to stop the sensor.
    except:
        #Error occurrred
        gbl_log.critical("[CTRL] Error occurred whilst looping to read values")
        print("\nCRITICAL ERROR during rading of sensor values- contact Support\n")
        gbl_log.exception("[CTRL] Start reading loop Exception Data")

    return

'''
As a node
get the message to be sent 
pass the reply in for checking
wait for the timeout
this needs to be looped and checked.

If not responded within time, reset to not Associated / resend the command


'''
def Node_Loop(op_info):
    """
    Perform the necessary functions to act as a node.
    """
    gbl_log.info("[CTRL] Starting Node Operation")
    try:
        comms = LoRa()
        sender = Node(op_info['node_addr'], op_info['hub_addr'])
        retries = SS.RETRIES
        data_to_send = False

        """
        if data_to_send == False:
            record_name, data_record = GetRecord()
            gbl_log.info("[CTRL] Record to send >%s< and its contents:%s" % ( record_name, data_record))
            if len(data_record) > 0:
                # pass in the data
                sender.set_data_to_be_sent(data_record)
                data_to_send = True
            else:
                data_to_send = False
        """
        while True:
            # Start the timer
            endtime = datetime.now() + timedelta(seconds=op_info['dir_read_freq'])
            print("\r\r\r\r\r\r\rReading", end="")

            # Loop round to get data and send it

            # get the message to send
            message = sender.message_to_send()
            gbl_log.info("[CTRL] Message To Send:%s" % message)
            # send the message
            status = comms.transmit(message)
            gbl_log.info("[CTRL] Message Send Status:%s" % status)
            # get and check the response
            reply = comms.receivetimeout(SS.REPLY_WAIT)
            gbl_log.info("[CTRL] Message Reply:%s" % reply)
            status = sender.check_response(reply)
            gbl_log.info("[CTRL] Message Reply Status:%s" % status)
            if status == True:
                retries = SS.RETRIES
                if data_to_send == True and sender.read_data_sent_status():
                    # if good, remove the record
                    RemoveRecordFile(record_name)
                    # check for more data
                record_name, data_record = GetRecord()
                if len(data_record) > 0:
                    sender.set_data_to_be_sent(data_record)
                    data_to_send = True
                else:
                    data_to_send = False
            else:
                # else drop out but increase the retries count.
                gbl_log.debug("[CTRL] Response status is negative, checking fo retry count")
                retries = retries - 1
                if retries == 0:
                    # Stop attempting to send the file and break out of the overall loop
                    data_to_send = False
                    sender.force_reassociation()
                    retries = SS.RETRIES
                else:
                    time.sleep(retries)        # Wait for a period before retrying

            if data_to_send == False:
                # Only have a delay if there is no data to send
                # Wait for timeout
                waiting = False
                while endtime > datetime.now():
                    if waiting == False:
                        print("\r\r\r\r\r\r\rWaiting", end="")
                        gbl_log.debug("[CTRL] Waiting for timeout to complete")
                        waiting=True
                    # Use time.sleep to wait without processor burn at 25%
                    sleep = datetime.now() - endtime
                    if sleep.total_seconds() > 2:
                        time.sleep(sleep.total_seconds() - 0.1)
                    else:
                        time.sleep(0.1)
        
    except KeyboardInterrupt:
        # CTRL - C entered
        print(" CTRL-C entered")
        gbl_log.debug("[CTRL] User Interrupt occurred (Ctrl-C)")
        gbl_log.info("[CTRL] End of Processing")

        #TODO: Need to add in some functionality here to stop the sensor.
    except:
        #Error occurrred
        gbl_log.critical("[CTRL] Error occurred whilst looping to read values")
        print("\nCRITICAL ERROR during rading of sensor values- contact Support\n")
        gbl_log.exception("[CTRL] Start reading loop Exception Data")

    return

def main():
    # The main program that calls all the necessary routines for the rest.

    SplashScreen()
    
    SetupLogging()

    args = SetandGetArguments()

    status, operational_info = LoadOperationalInfo()
    if status != True:
        print("Operational Infomation is missing or incomplete, please re-enter")
        operational_info = SetOperationalParameters()


    if args.hub:
        Hub_Loop(operational_info)
    elif args.node:
        Node_Loop(operational_info)
    elif args.displayinfo:
        DisplayOperationalParameters(operational_info)
    elif args.setinfo:
        SetOperationalParameters()
    else:
        Hub_Loop(operational_info)

    return
# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    
    try:
        main()
    
    except:
        # This won't work as it requires knowledge of the instances
        LoRa.exit_hub()
        Hub.exit_comms()
        print("Program Ended...")
        sys.exit()
