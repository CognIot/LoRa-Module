#!/usr/bin/env python3
'''
This program provides a ELB module simulator to test the main LoRa program

For more info see www.CognIot.eu

This operates at the lowest level possible, without actual comms down the serial port.

The LoRaComms class can opoerate in test mode:
    self.normal_mode = False
    When writing to serial port
        self.test_write is set to the bytes sent
    When reading form the serial port (all)
        self.test_read_flag must be set when data ready to be read
        self.test_read contains the data to be read
    When reading form the serial port (length)
        self.test_read_length is set to the number of bytes expected
        self.test_read_flag must be set when data ready to be read
        self.test_read contains the data to be read

This operates at the lowest level possible, without actual comms down the serial port.

It is not implemented at this time - this version runs on a separate Pi.

'''
#TODO: Handle the LED

import serial
import logging
import time
import math
import sys
import random
import RPi.GPIO as GPIO


# setup the serial port
# respond to setup of LoRa comms
# respond to the normal commands

# Define the test connection details
INPUT_PIN = 17
LED_PIN = 23

INTERDELAY = 0.3

# LoRa Commands
NS_SENDB = b'AT+X'                     # Send a stream of n bytes long
NS_REC_LEN = b'AT+r'                   # Return the received length of data
NS_RESET = b'AT!!'                     # Reset the LoRa module
NS_VERSION = b'AT*v'                   # Read the version of the LoRa module
NS_GLORA =  b'AT*q'                    # Display the current configuration
NS_SLORAMODE_ONE = b'sloramode 1'      # Start the LoRa module at 868MHz

def ns_setup_gpio():
    # Setup the GPIO for the reading of the incoming data
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    time.sleep(0.2)
    GPIO.setup(INPUT_PIN, GPIO.IN)
    GPIO.setup(LED_PIN, GPIO.OUT)
    logging.debug("[SIM]: GPIO Setup Complete")
    return

def ns_setup_uart():
    """
    Setup the UART for communications and return an object referencing it. Does:-
    -Initiates serial software
    -Opens the serial port
    -Checks all is ok and returns the object
    """
    try:
        ser = serial.Serial('/dev/serial0',
                            baudrate=57600,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS,
                            timeout=0.1)
    except:
        logging.critical("[SIM]: Unable to Setup communications on Serial0, trying ttyAMA0")
        ser = ''

    if ser =='':
        try:
            ser = serial.Serial('/dev/ttyAMA0',
                                baudrate=57600,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                bytesize=serial.EIGHTBITS,
                                timeout=0.1)
        except:
            logging.critical("[SIM]: Unable to Setup communications on ttyAMA0")
            sys.exit()

    time.sleep(INTERDELAY)

    # clear the serial buffer of any left over data
    ser.flushInput()

    if ser.isOpen():
        # if serial comms are setup and the channel is opened
        logging.info ("[SIM]: PI UART setup complete on channel %d as : %s" % (ser.fd, ser.getSettingsDict))
    else:
        logging.critical("[SIM]: Unable to Setup communications")
        sys.exit()
    return ser

def ns_get_sent(fd):
    # Get the data over the UART and return it. Waits until there is data to read.
    reply = b''
    while len(reply) < 1:
        try:
            reply = fd.readall()

#BUG: I think this is returing all the data in 1 shot and not the first slash n.
#       Could it be the readall is waiting too long, or the data sent is sent too quick.
        except:
            logging.warning("[SIM]: Reading of data on the serial port FAILED")
            reply = b''

    logging.debug("[SIM]: Data received over the serial port :%s" % reply)
    return reply

def ns_send_back(fd, send):
    # Send the data given back over the UART
    try:
        ans = fd.write(send)
        logging.info("[SIM]: Message >%s< written to LoRa module and got response :%s" % (send, ans))
    except Exception as e:
        logging.warning("[SIM]: Message >%s< sent FAILED" % (send))
        ans = 0
    return ans

def positive_response():
    # Construct a positive response
    pos_rsp = b'\n\rOK00>'
    return pos_rsp

def build_command(cmd):
    # Take the given command and build the string around it
    # return the binary string
    first_part = b'\r\n'
    expected = first_part + cmd + positive_response()

#BUG: The built string is incorrect, need to check what is actually sent from the log files

    return expected

def ns_wake_up(fd):
    # Handle the wakeup sequence
    # LCR sends \n repeatably until a psoitive response
    boot_time = random.randint(0,2000) / 1000       # set the wait time, in mS
    reply = b''
    # Wait for first \n
    logging.debug("[SIM]: Waiting for the first \\n sent")
    while reply != b'\n':
        print("reply:%s" % reply)
        reply = ns_get_sent(fd)
    logging.debug("[SIM]: Seen the first \\n sent")

    # Wait for a random period of time
    starttime = time.timer() + boot_time
    while time.timer() < starttime:
        time.sleep(0.001)
    logging.debug("[SIM]: Waited for a random time: %s mS" % boot_time)

    # reply with positive response
    ns_send_back(fd, positive_response())

    return

def ns_handle_config_cmd(fd, cmd):
    # Handle the reset command that is received.
    reset_time = random.randint(0,2000) / 1000       # set the wait time, in mS
    reply = b''
    logging.debug("[SIM]: Waiting for the %s command" % cmd)
    while reply != build_command(cmd):
        reply = ns_get_sent(fd)
    logging.debug("[SIM]: Seen the %s command" % cmd)

    # Wait for a random period of time
    starttime = time.timer() + reset_time
    while time.timer() < starttime:
        time.sleep(0.001)
    logging.debug("[SIM]: Waited for a random time: %s mS" % reset_time)

    # reply with positive response
    ns_send_back(fd, positive_response())
    return

def ns_setup_lora(fd):
    # Handle the setup commands expected for a module.
    # Expected command sequence
    ns_wake_up(fd)
    ns_handle_config_cmd(fd,NS_RESET)
    ns_handle_config_cmd(fd,NS_VERSION)
    ns_handle_config_cmd(fd,NS_SLORAMODE_ONE)
    ns_handle_config_cmd(fd,NS_GLORA)
    return

def responses(fd):
    # Main routine to handle incoming messages and respond accordingly.
    while(True):
        msg = ns_get_sent(fd)
        #TODO: Add command decoding here
    return

def main():
    # Main function to be run to manage the test routines.
    port = ns_setup_uart()
    ns_setup_gpio()

    ns_wake_up(port)
    ns_setup_lora(port)

    #TODO: From this point, the command beig received could be one of many and therefore
    #       needs to be in a loop similar to the main program

    return


if __name__ == '__main__':
    logging.basicConfig(filename="NodeSimulator.txt", filemode="w", level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(message)s')

    main()


