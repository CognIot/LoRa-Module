#!/usr/bin/env python3
"""
This program is used to listen to the LoRa transmissions

It is intended to be used as part of the LoRa Monitor.

There are hooks for testing purposes defined, see below

These hooks can't be used unless threading is instigated.
"""

import serial
import logging
import time
import math
import sys
import random
import RPi.GPIO as GPIO

# use _name for non public methods

# The connected GPIO pin to indicate when the LoRa module has data to read
INPUT_PIN = 17

# During processing of LoRa messages, there is a timeout to determine if the message is old
# This is measured in seconds
COMMS_TIMEOUT = 2

# LoRa Commands
SENDB = b'AT+X'                     # Send a stream of n bytes long
REC_LEN = b'AT+r'                   # Return the received length of data
RESET = b'AT!!'                     # Reset the LoRa module
VERSION = b'AT*v'                   # Read the version of the LoRa module
GLORA =  b'AT*q'                    # Display the current configuration
SLORAMODE_ONE = b'sloramode 1'      # Start the LoRa module at 868MHz

class LoRaComms:
    '''
    Class to handle all communicaitons with the LoRa module
    This class handles all the comms, it is not ELB specific
    
    Any data passed in or out needs to be in binary format

    '''
    
    def __init__(self, mode=True):
        # initialise the comms for the module
        self.fd = _setup_uart()
        _setup_gpio()
        _setup_lora()
        self.normal_mode = mode        # When set to False, the Comms module will operate in a test mode.
        
    def transmit(self, message):
        # Send data out on the comms port
        # Returns True if successful or Flase if not
        
        if len(message) > 255:
            # Length is greater than 255, abort.
            logging.critical("[LCR]: Radio Message length is greater than 255 limit, aborting: %s" % message)
            return False

        # Message to send is AT+X plus a space plus the length in 2 char hex, all encoded in binary string format
        reply = _write_to_sp(SENDB + ' ' + format(len(message), '02X').encode('utf-8'))
        if reply > 0:
            reply = _read_from_sp()
            if _check_for_dollar(reply):
                if _write_to_sp(message) > 0:
                    reply = _read_from_sp()
                    if _check_lora_response(reply):
                        return True
        return False    
        
    def receive(self):
        # Receive data on the comms port and return it to the calling program
        # NOTE: It can return zero bytes if there is no data to read

        # TODO: Do I wait for the data pin to be high and the data length to be greater than zero??
        _wait_for_gpio()
        length = _get_data_length()
        if length > 0:
            reply = _read_from_sp(length)
            if _check_lora_response(reply):
                data = _strip_out_data(reply, length)
                if data['success']:
                    return data['reply']
        return b''
    
    def exit_comms(self):
        # This routine is called on the exit of the main program
        GPIO.cleanup()
        if self.normal_mode:
            self.fd.close()
        return

    ## The functions below here are for internal use within the class only
    
    def _write_to_sp(self, data_to_transmit):
        # Write the given data to the serial port
        # Returns the data length or 0 if failed
        # add the control characters
        send = data_to_transmit + b'\r\n'
        try:
            if self.normal_mode:
                ans = self.fd.write(send)
            else:
                self.test_write = send
            logging.info("[LCR]: Message >%s< written to LoRa module and got response :%s" % (data_to_transmit, ans))
        except Exception as e:
            logging.warning("[LCR]: Message >%s< sent as >%a< FAILED" % (data_to_transmit, send))
            _led_error()
            ans = 0
        return ans
    
    def _read_from_sp(self, length=-1):
        # Read data from the serial port, using length if given
        # return the data, length of zero if nothing of failed
        try:
            if length == -1:
                if self.normal_mode:
                    reply = self.fd.readall()
                else:
                    while self.test_read_flag = False:
                        time.sleep(0.01)
                    reply = self.test_read
            else:
                if self.normal_mode:
                    reply = self.fd.read(length)
                else:
                    self.test_read_length = length
                    while self.test_read_flag = False:
                        time.sleep(0.01)
                    reply = self.test_read
        except:
            logging.warning("[LCR]: Reading of data on the serial port FAILED")
            reply = b''
            _led_error()

        logging.debug("[LCR]: Data read back from the serial port :%s" % reply)
        return reply
        
    def _led_error(self):
        # Flash the LED for an error state
        return
        
    def _check_for_dollar(self, receive):
        # Given the response, check for the $
        # A positive response is b'\r\n$'
        if b'$' in receive:
            return True
        else:
            return False

    def _check_lora_response(self, receive):
        # For the given response, check the lora reply is a positive reply
        # return True if it is, else False if it isnt, capturingn the error message
        # A good response will have OK00 before the '>' prompt
        response_posn = 5       # The position of the response from the end
        if len(receive) < response_posn:
            logging.warning("[LCR]: Length of response received is too short:%s" % receive)
            return False
    
        if b'OK00' in receive[len(receive) - reponse_posn:]:
            return True
        else:
            response = receive[len(receive) - response_posn:]
            logging.warning("[LCR]: Negative response received from the LoRa module:%s" % response)
            return False
    
    def _setup_uart(self):
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
            logging.critical("[LCR]: Unable to Setup communications")
            sys.exit()
    
        time.sleep(INTERDELAY)
    
        # clear the serial buffer of any left over data
        ser.flushInput()
    
        if ser.isOpen():
            # if serial comms are setup and the channel is opened
            logging.info ("[LCR]: PI UART setup complete on channel %d as : %s" % (ser.fd, ser.getSettingsDict))
        else:
            logging.critical("[LCR]: Unable to Setup communications")
            sys.exit()
        return ser

    def _setup_gpio(self):
        # Setup the GPIO for the reading of the incoming data
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        time.sleep(0.2)
        GPIO.setup(INPUT_PIN, GPIO.IN)
        GPIO.setup(LED_PIN, GPIO.OUT)
        logging.debug("[LCR]: GPIO Setup Complete")
        return

    def _setup_lora(self):
        # Setup the LoRa module configuration
        logging.info("[LCR]: Setting up the LoRA module with the various commands")
        _lora_module_wakeup()
    
        _send_config_command(RESET)
        time.sleep(INTERDELAY)
        time.sleep(INTERDELAY)
    
        _send_config_command(VERSION)
        time.sleep(INTERDELAY)
        _send_config_command(SLORAMODE_ONE)
        time.sleep(INTERDELAY)
        _send_config_command(GLORA)
        return

    def _wait_for_gpio(self):
        # Routine monitors the GPIO pin and waits for the line to go high indicating a packet.
        logging.debug("[LCR]: Waiting for data pin to go high")
        logging.info(" ")       # Add blank line for readability of the log file
    
        status = 0
        while(status!=1):
            status = GPIO.input(INPUT_PIN)
        logging.debug("[LCR]: Data Pin gone high at time :%s" % time.strftime("%d-%m-%y %H:%M:%S"))
        return
    
    def _get_data_length(self):
        # Send the REC_LEN (AT+r) and decode the response to get the length of the data
        # return the length, or zero on fail
        length = 0
        if _write_to_sp(REC_LEN) > 0:
            # Expect to get 'xx\r\nOK00>' where xx is the length byte
            reply = _read_from_sp(9)
            if _check_lora_response(reply):
                length = int(reply[0:2], 16)
        return length
    
    def _strip_out_data(self, message, length):
        # given the message of data, strip out the data and return it
        # Returns a dictionary of the True / False and the stripped out data
        ans = b''

        if len(message) < length:
            # The data returned is shorter than expected, return failed
            logging.warning("[LCR]: Reply shorter than expected from the LoRa module")
            return {'success':False, 'reply':ans}

        # Populate the first part of the data (ans) with the data
        ans = reply[0:length]
        logging.info("[LCR} - Data of length >%s< read from the Serial port: %a" % (length, ans))
        return {'success':True, 'reply':ans}

    def _lora_module_wakeup(self):
        # This function sends data and gets the reply for the various configuration commands.
        logging.info("[LCR]: Waking up the LoRa module")
        command =b'\n'
        working = False
        starttime = time.time()
        while (starttime + COMMS_TIMEOUT > time.time()) and working == False:
            ans = _write_to_sp(command)
            if ans >0:
                time.sleep(SRDELAY)
                # No need to check the reply as it has already been validated
                reply = _read_from_sp(length)
                working = _check_lora_response(reply)
            else:
                logging.warning("[LCR]: Failed to Send Config Command %s" % command)
                _led_error()
        return
    
    def _send_config_command(command):
        # This function sends data and gets the reply for the various configuration commands.
        ans = _write_to_sp(command)
        if ans > 0:
            #time.sleep(SRDELAY)
            reply = _read_from_sp(length)
            if _check_lora_response(reply):
                logging.debug("[LCR]: Sent Config Command successfully: %s" % command)
                return
        logging.warning("[LCR]: Failed to Send Config Command %s" % command)
        _led_error()
        return

    ## These functions are used by the LoRaComms test routines to validate the code above.
    ''' For Test mode
            self.normal_mode = False
            When writing to serial port
                self.test_write is set to the bytes sent
            When reading form the serial port (all)
                self.test_read_flag must be set when data ready to be read
                self.test_read contains the data to be read
            When reading form the serial port (length)
                self.test_read_length is set to the number of bytes expected
                self.test_read_flag must be set when data ready to be read
                self.test_read contains the data to be read'''

    def test_write(self):
        return self.test_write
    
    def test_read_flag(self, flag):
        self.test_read_flag = flag
        return
        
    def test_read(self, value):
        self.test_read = value
        return
    
    def test_read_length(self):
        return self.test_read_length
    
    

# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    # Do something!
    print("doing something")



