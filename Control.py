#!/usr/bin/env python3
"""
This program is used to control the communications between the Hub and the Node


"""

import sys

import LoRaCommsReceiverV2 as LoRa
import HubDataDecoderV2 as Hub
import Standard_settings as SS
#import LogFileWriter

# This will need to set the HUB address??

def SetandGetArguments():
    """
    Define the arguments available for the program and return any arguments set.

    """

    gbl_log.info("[CTRL] Setting and Getting Parser arguments")
    parser = argparse.ArgumentParser(description="Set the functionality for transferring data using LoRa")
    Main_group = parser.add_mutually_exclusive_group()
    Main_group.add_argument("-h", "--hub", action="store_true",
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

def SetOperationalParameters(device):
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
    op_info['device'] = device
    gbl_log.debug("[CTRL] Device Number:%s" % device)

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

    SaveOperationalInfo(op_info)

    #TODO: Add in setting of the sensor info at this stage?
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

def LoadOperationalInfo(dev):
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

    opfile['device'] = dev        #device_id is set by the UUID of the Pi

    # Validate the operational info that has been read back.
    status = True
    for item in ['dir_read_freq']:
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


    """
#TODO: Do somethign!!!


    return
    
def Hub(op_info):
    """
    Perform the necessary functionality to operate as a Hub
    """
    gbl_log.debug("[CTRL] Starting Hub Operation"))
    try:
        comms = LoRa()
        decode = Hub(op_info['hub_addr'], op_info['node_addr']
        while True:
            message = comms.receive()
            decode.incoming(message)
            if decode.reply_status:
                if decode.reply_payload_len() > 0:
                    WriteDataToDir(decode.reply_payload())
                message = comms.transmit(decode.reply())
                


    except KeyboardInterrupt:
        # CTRL - C entered
        print(" CTRL-C entered")
        gbl_log.debug("[CTRL] User Interrupt occurred (Ctrl-C)")
        icog.EndReadings()
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

    status, operational_info = LoadOperationalInfo(device_id)
    if status != True:
        print("Operational Infomation is missing or incomplete, please re-enter")
        operational_info = SetOperationalParameters(device_id)


    if args.hub:
        Hub(operational_info)
    elif args.node:
        Node(operational_info)
    elif args.displayinfo:
        DisplayOperationalParameters(operational_info)
    elif args.setinfo:
        SetOperationalParameters(device_id)
    else:
        Hub()

    return

# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    logging.basicConfig(filename="HubDecoder.txt", filemode="w", level=LG_LVL,
                        format='%(asctime)s:%(levelname)s:%(message)s')


    try:
        main()
    
    except:
        # This won't work as it requires knowledge of the instances
        LoRa.exit_hub()
        Hub.exit_comms()
        print("Program Ended...")
        sys.exit()
