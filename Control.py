#!/usr/bin/env python3
"""
This program is used to control the communications between the Hub and the Node


"""

import sys

from LoRaCommsReceiverV2 import LoRaComms as LoRa
from HubDataDecoderV2 import NODE as Receiver
import Standard_Settings as SS
import json
import os
import logging
import logging.config
import dict_LoggingSetup
import argparse

#BUG: This can only handle 127 bytes, so the data transferred is 
# This will need to set the HUB address??

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

#TODO: Set the right parameters
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
        choice = input("Please enter the Hub Address? ")
        if choice.isdigit():
            choice = int(choice)
            op_info['hub_addr'] = choice
        else:
            print("Please enter a number")
            choice = ""
    gbl_log.debug("[CTRL] Hub Address:%s" % choice)

    choice = ""
    while choice == "":
        choice = input("Please enter the Node Address? ")
        if choice.isdigit():
            choice = int(choice)
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
    self.log.info("[DAcc] Writing new record to disk:%s" % data_record_name)

    #TODO: Need to handle a failure to open the file
    with open(data_record_name, mode='w') as f:
        json.dump(data_to_write, f)
        status = True
    return status

    return

def CheckForData():
    """
    Check for files in the directory, return True or False
    """

#TODO: Need to complete this

    return

def SendRecord(lora, decoder, record):
    """
    Taken the given record contents, send it 
    """
    retries = SS.RETRIES
    data_sent = False
    while data_sent == False and retries > 0:
        # timer is handed by the LoRa comms layer
        gbl_log.info("[CTRL] Starting Record Send")

        # Send association request
        msg = decoder.outgoing_DataPack(record)
        status = lora.transmit(msg)

        if status:
            # Wait for repsonse within timeout
            reply = lora.receivetimeout(SS.REPLY_WAIT)

            #check for the correct reply
            #TODO: Need a method to validate NODE incoming messages
            if len(reply) > 11:
                gbl_log.debug("[CTRL] Message received is greater than the miminum length")
                if reply[10] == chr(0x22).encode('utf-8'):
                    #Data Sent
                    gbl_log.debug("[CTRL] Message received has ACK command byte")
                    data_sent=True
                else:
                    retries = retries - 1
                    gbl_log.debug("[CTRL] reply[10] didn't contain 0x22")
            else:
                retries = retries - 1
                gbl_log.debug("[CTRL] length of reply was less than 11 characters")
        else:
            # Failed to send message.
            retries = retries - 1
            gbl_log.debug("[CTRL] LoRa Comms returned a negative response")
    return data_sent
    
def RemoveRecordFile(record_to_remove):
    """
    Remove the file from the directory
    """

    if os.path.isfile(SS.RECORDFILE_LOCATION+'/' + record_to_remove):
        os.remove(SS.RECORDFILE_LOCATION+'/' + record_to_remove)
        gbl_log.info("[CTRL] Record File deleted:%s" % SS.RECORDFILE_LOCATION+'/' + record_to_remove)
    return

def RenameRecordFile(record_to_rename):
    """
    Rename the current file to the old name so it is no longer sent
    """
    if os.path.isfile(SS.RECORDFILE_LOCATION+'/' + record_to_rename):
        os.rename(SS.RECORDFILE_LOCATION+'/' + record_to_rename, SS.RECORDFILE_LOCATION+'/' + record_to_rename[-3:] + SS.RECORDFILE_OLD)
        gbl_log.info("[DAcc] Record File renamed:%s" % SS.RECORDFILE_LOCATION+'/' + record_to_rename[-3:] + SS.RECORDFILE_OLD)
    return
        
def SendData(lora, decoder):
    """
    Take all the files in the directory and send them one at a time
    Given the LoRa class and the Decoder class to use
    Needs to handle association as well as data sending
    """

    gbl_log.info("[CTRL] Getting the list of files to use and selecting one")
    status = False
    list_of_files = os.listdir(path=SS.RECORDFILE_LOCATION+'/.')
    list_of_files.sort()
    gbl_log.debug("[CTRL] Files to Use :%s" % list_of_files)
    for record_to_use in list_of_files:
        gbl_log.debug("[CTRL] File being checked for extension of %s:%s" % (SS.RECORDFILE_EXT, i))
        if i[-len(SS.RECORDFILE_EXT):] == SS.RECORDFILE_EXT:
            with open(file_name, mode='r') as f:
                record = json.load(f)
                #BUG: The line above is reading [] and assuming it is a string and not a list!
                gbl_log.debug("[CTRL] Record loaded for use:%s" % record)
            
                if len(record) > 0:
                    gbl_log.debug("[CTRL] Length of record:%s" % len(record))
                    status = SendRecord(lora,decoder,record)
                    if status == True:
                        RemoveRecordFile(record_to_use)
                        record_try_count = 0
                    else:
                        record_try_count = record_try_count + 1
                        if record_try_count > SS.RECORD_TRY_COUNT:
                            gbl_log.error("[CTRL] Failed to send record over %s times, record archived" % record_try_count)
                            gbl_log.info("[CTRL] Archived Record:%s" % record)
                            RenameRecordFile(record)
                        else:
                            time.sleep(record_try_count)        # Wait for a period before retrying
                else:
                    more_data = False
                    gbl_log.info("[CTRL] No more data records to read")
    return status

def GetAssociated(lora, decoder):
    """
    Perform the necessary actions to get associated
    returns True is successful, False if not
    The timing is handled by the LoRa module
    """
    #RETRIES outer loop
    retries = SS.RETRIES
    assocaited = False
    while associated == False and retries > 0:
        # timer is handed by the LoRa comms layer
        gbl_log.info("[CTRL] Starting association")

        # Send association request
        msg = decoder.outgoing_AssociateRequest()
        status = lora.transmit(msg)

        if status:
            # Wait for repsonse within timeout
            reply = lora.receivetimeout(SS.REPLY_WAIT)

            #check for the correct reply
            #TODO: Need a method to validate NODE incoming messages
            if len(reply) > 11:
                gbl_log.debug("[CTRL] Message received is greater than the miminum length")
                if reply[10] == chr(0x31).encode('utf-8'):
                    #Associated
                    gbl_log.debug("[CTRL] Message received has correct command byte")
                    associated=True
                else:
                    retries = retries - 1
                    gbl_log.debug("[CTRL] reply[10] didn't contain 0x31")
            else:
                retries = retries - 1
                gbl_log.debug("[CTRL] length of reply was less than 11 characters")
        else:
            # Failed to send message.
            retries = retries - 1
            gbl_log.debug("[CTRL] LoRa Comms returned a negative response")
    return associated
    
def Hub(op_info):
    """
    Perform the necessary functionality to operate as a Hub
    """
    gbl_log.info("[CTRL] Starting Hub Operation")
    try:
        comms = LoRa()
        decode = Receiver(op_info['hub_addr'], op_info['node_addr'])
        while True:
            message = comms.receive()
            gbl_log.debug("[CTRL] Message received from the comms:%s" % message)
            decode.incoming(message)
            if decode.reply_status:
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

def Node(op_info):
    """
    Perform the necessary functions to act as a node.
    """
    gbl_log.info("[CTRL] Starting Node Operation")
    associated = False
    try:
        comms = LoRa()
        decode = Receiver(op_info['hub_addr'], op_info['node_addr'])
        while True:
            # Start the timer
            endtime = datetime.now() + timedelta(seconds=op_info['dir_read_freq'])
            print("\r\r\r\r\r\r\rReading", end="")

            if associated == False:
                associated = GetAssociated(comms, decode)

            if associated:
                if CheckForData():
                    # If there is a file to send, send it
                    SendData(comms, decode)

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
        Hub(operational_info)
    elif args.node:
        Node(operational_info)
    elif args.displayinfo:
        DisplayOperationalParameters(operational_info)
    elif args.setinfo:
        SetOperationalParameters()
    else:
        Hub(operational_info)

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
