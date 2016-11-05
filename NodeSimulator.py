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

# Define the wait time during a packet transmission to wait for a new byte
STARTTOEND = 0.1

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

def set_gpio(state):
    # Set the GPIO pin to the required state.
    GPIO.output(INPUT_PIN, state)
    return
    
def reset_gpio():
    # Reset the GPIO pin back to the normal level after a time period.
    time.sleep(0.25)
    set_gpio(False)
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

            print("Reply:%s" % reply)       # Additional debug

        except:
            logging.warning("[SIM]: Reading of data on the serial port FAILED")
            reply = b''

    logging.debug("[SIM]: Data received over the serial port :%s" % reply)
    return reply

def ns_get_byte_sent(fd):
    # Get the data over the UART and return it. Waits until there is data to read.
    reply = b''
    while len(reply) < 1:
        try:
            reply = fd.read(1)

#BUG: I think this is returing all the data in 1 shot and not the first slash n.
#       Could it be the readall is waiting too long, or the data sent is sent too quick.
        except:
            logging.warning("[SIM]: Reading of data on the serial port FAILED")
            reply = b''

    logging.debug("[SIM]: Data received over the serial port :%s" % reply)
    return reply

def ns_get_packet(fd):
    # Getting them 1 byte at a time, get the packet on the buffer
    # Uses a timeout to decide when it has all packets
    packet = b''                # the full packet being returned
    reply = b''                 # The byte received
    first_byte_time = 0         # The time the first byte was received
    all_data = False            # Set tp True when all data received
    # sit in a loop waiting for the data to be received
    #   Set the timeout to start after the first byte
    #   Set all_data to true on timeout
    
    while all_data == False:
        # Get the data from the serial port
        #try:
            #reply = fd.read(1)
            #logging.debug("[SIM]: Got a byte of data:%s" % reply)
        #except:
            #logging.debug("[SIM]: NO data returned on the serial port")
            #reply = b''
        if fd.inWaiting() > 0:
            reply = fd.read(1)
            logging.debug("[SIM]: Got a byte of data:%s" % reply)
        else:
            reply =b''
        # Check if there is anything
        if len(reply) > 0:
            # Set first_byte time if not set
            if first_byte_time == 0:
                first_byte_time = time.time()
                logging.debug("[SIM]: Seen the first byte at time: %s" % time.strftime("%H:%M:%S", time.localtime(first_byte_time)))
                #           Formatted the time in seconds to a HH:MM:SS
            packet = packet + reply
            reply = b''                 # Reset for the next byte
        else:
            # check if timeout, and if data, set all_data to true
            if first_byte_time + STARTTOEND > time.time():
                all_data = True
                logging.debug("[SIM]: It has been %s seconds since the last byte was received" % STARTTOEND)
            
    return packet
    
def ns_send_back(fd, send):
    # Send the data given back over the UART
    try:
        ans = fd.write(send)
        logging.info("[SIM]: Message >%s< written to LoRa module and got response :%s" % (send, ans))
    except Exception as e:
        logging.warning("[SIM]: Message >%s< sent FAILED" % (send))
        ans = 0
    return ans

def ns_send_back_gpio(fd, send):
    # Send the data given back over the UART
    # Set the GPIO pin high afterwards
    set_gpio(False)
    try:
        ans = fd.write(send)
        logging.info("[SIM]: Message >%s< written to LoRa module and got response :%s" % (send, ans))
    except Exception as e:
        logging.warning("[SIM]: Message >%s< sent FAILED" % (send))
        ans = 0
    set_gpio(True)
    return ans
    
def positive_response():
    # Construct a positive response
    pos_rsp = b'\n\rOK00>'
    return pos_rsp

def build_command(cmd):
    # Take the given command and build the string around it
    # return the binary string
    second_part = b'\r\n'
    expected = cmd + second_part
    return expected

def ns_wake_up(fd):
    # Handle the wakeup sequence
    # LCR sends \n repeatably until a positive response
    boot_time = random.randint(0,2000) / 1000       # set the wait time, in mS
    reply = b''
    # Wait for first \n
    logging.debug("[SIM]: Waiting for the first \\n sent")
    while reply != b'\n':
        reply = ns_get_byte_sent(fd)
    logging.debug("[SIM]: Seen the first \\n sent")

    # Wait for a random period of time
    starttime = time.time() + boot_time
    while time.time() < starttime:
        time.sleep(0.001)
    logging.debug("[SIM]: Waited for a random time: %s mS" % boot_time)

    # reply with positive response
    ns_send_back(fd, positive_response())

    fd.flushInput()

    return

def ns_handle_config_cmd(fd, cmd):
    # Handle the reset command that is received.
    reset_time = random.randint(0,500) / 1000       # set the wait time, in mS
    reply = b''
    logging.debug("[SIM]: Waiting for the %s command" % cmd)
#    while reply != build_command(cmd):
    while build_command(cmd) not in reply:
        #reply = ns_get_sent(fd)
        #reply = reply + ns_get_byte_sent(fd)
        reply = ns_get_packet(fd)
    logging.debug("[SIM]: Seen the %s command" % cmd)

    # Wait for a random period of time
    starttime = time.time() + reset_time
    while time.time() < starttime:
        time.sleep(0.001)
    logging.debug("[SIM]: Waited for a random time: %s S" % reset_time)

    # reply with positive response
    ns_send_back(fd, positive_response())
    return

def ns_setup_lora(fd):
    # Handle the setup commands expected for a module.
    # Expected command sequence
    ns_wake_up(fd)
    
    #TODO: Need to handle repeats of the commands, build something similar to the decode routine in HubDataDecoder
    ns_handle_config_cmd(fd,NS_RESET)
    ns_handle_config_cmd(fd,NS_VERSION)
    ns_handle_config_cmd(fd,NS_SLORAMODE_ONE)
    ns_handle_config_cmd(fd,NS_GLORA)
    return

def ns_reply_with_sent(fd):
    # Read what has been received and send it straight back.
    
    while True:
        ns_received = ns_get_packet(fd)
        time.sleep(random.randint(0,500) / 1000)
        ns_send_back_gpio(fd, ns_received)
        reset_gpio()

def main():
    # Main function to be run to manage the test routines.
    port = ns_setup_uart()
    ns_setup_gpio()

    ns_setup_lora(port)

    #From this point, the command being received could be one of many and therefore it is simply sent
    # back after a random time
    
    ns_reply_with_sent(port)

    return


if __name__ == '__main__':
    logging.basicConfig(filename="NodeSimulator.txt", filemode="w", level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(message)s')

    '''
    port = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=3.0)

    while True:
        rcv = port.readall()
        print("Received:%s" % rcv)
    '''
    main()


