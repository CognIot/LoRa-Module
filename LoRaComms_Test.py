#!/usr/bin/env python3
'''
This program provides a LoRa Comms Receiver Test module. It needs to be run in conjunction with
the Node Simulator.

For more info see www.CognIot.eu

Functionality.


'''

import logging
import LoRaCommsReceiverV2 as LCR_V2
import random

# Set a default header to the messages
HEADER = b'!ABCD!\xff'

# setup the serial port
# respond to setup of LoRa comms
# respond to the normal commands

def generate_message(lora, size):
    # Generate the message of the given size, max is 127 characters
    lt_msg = ''
    for byte in range(0,256):
        lt_msg = lt_msg + chr(byte)

    lt_msg = lora + HEADER + lt_msg[0:size].encode('utf-8')
    return lt_msg

def generate_ctrl_codes_mgs(lora, size):
    # Generate a message using the various control codes
    codes = b'\r\nOK00>$'
    lt_msg = b''
    for char in range(0, size):
        lt_msg = lora + HEADER + lt_msg + chr(codes[random.randint(0,len(codes)-1)]).encode('utf-8')
    return lt_msg

def build_list(addr):
    # Build a list of the commands to send and expected responses
    # Return a list of lists
    # Inner list contains: "test", packet to send, expected response
    
    build = []
    # Send message of length 1 to 255, get back the same
    for i in range(0,256):
        msg = generate_message(addr, i)
        build.append(["Message test %s" % i, msg, msg])
    
    # Send messages of fixed length of 10 characters, but including the control characters, 10 random ones
    for i in range(0,10):
        msg = generate_ctrl_codes_mgs(addr, 10)
        build.append(["Control Code Messages %s" % i, msg, msg])
        
    # Return LoRa error codes
    
    # Some non responses
    
    # LoRa module not returning $
    #   Send a special string to the simulator and it can then not return anything.
    
    return build
    

def main():
    # Main function to be run to manage the test routines.

    # Designed to run multiple instances of the code, but this can't work with only 1 receiver software
    # as it currently stands
    #lora_list = []
    #lora_list = [b'1234', b'2345', b'3456', b'4567', b'5678', b'6789', b'7890']
    #scenarios = {}
    #loras = {}

    ## Build a list of nodes and associated scenarios
    #for lora in lora_list:
        #instance = LCR_V2.LoRaComms()
        #loras.update({lora: instance})
        #lora_scenarios = build_list(lora)
        #scenarios.update({lora:lora_scenarios})





    # The command below will instigate comms
    lora = LCR_V2.LoRaComms()
    
    for message in build_list():
        sent_ok = lora.transmit(message[1])
        if sent_ok:
            get_back = lora.receive()
            if get_back == message[2]:
                print("." % message[0], end="")
            else:
                print("\nTest:%s FAILED\n" % message[0])
                time.sleep(1)


    lora.exit_comms()



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

