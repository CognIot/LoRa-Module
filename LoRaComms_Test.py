#!/usr/bin/env python3
'''
This program provides a LoRa Comms Receiver Test module. It needs to be run in conjunction with
the Node Simulator.

For more info see www.CognIot.eu

Functionality.


'''

import logging
import LoRaCommsReceiverV2 as LCR_V2

# setup the serial port
# respond to setup of LoRa comms
# respond to the normal commands

# Define the test connection details

def main():
    # Main function to be run to manage the test routines.

    # This program
    loras = {}
    # The command below will instigate comms
    lora = LCR_V2.LoRaComms()



if __name__ == '__main__':
    logging.basicConfig(filename="LoRaComms_Test.txt", filemode="w", level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(message)s')

    import serial
    import time

    '''
    port = serial.Serial("/dev/serial0", baudrate=57600, timeout=3.0)
    while True:
        port.write(b'\r\nSay something')
        time.sleep(1)
        print("Sent")
    '''
    main()

