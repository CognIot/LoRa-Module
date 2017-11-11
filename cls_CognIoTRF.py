#!/usr/bin/env python3
"""
Bostin Technology  (see www.CognIoT.eu)

A collection of classes that provide the necessary functions to support

    CognIoT RF Specification V1.0

File consists of 3 classes
- Common        - Contains all the common functions to be used, not called separately
                    Called by the 2 classes below
- Hub           - Handles the incoming message and generates the necessary responses
- Node          - provides teh functions to run as a node

"""

import logging
import time

# Pointers to the position of the parts of the packet
START_HUB_ADDR = 0          # Position in packet where hub address starts
HUB_CONTROL_BYTE = 4        # Position of the Hub Control byte
START_NODE_ADDR = 5         # Position in packet where node starts
NODE_CONTROL_BYTE = 9       # Position of the Node Control byte
COMMAND = 10                # Position in packet where the command byte is
PAYLOAD_LEN = 11            # Position in packet where the payload length byte is
PAYLOAD = 12                # Position in packet where the payload starts


#TODO: Change all these to all capitals with underscores

# Constants that will not change in program
# Command bytes that are used by protocol
AssociationRequest = chr(0x30).encode('utf-8')
AssociationResponse = chr(0x31).encode('utf-8')
DataPacket = chr(0x37).encode('utf-8')
Ping = chr(0x32).encode('utf-8')

# Response codes
ACK = chr(0x22).encode('utf-8')                 # all good and confirmed
NACK = chr(0x99).encode('utf-8')                # General NACK response


# initialise global variables for data packet. Defined here so that they are global
Packet = b''  # start with empty packet.
ZeroPayload = chr(0x00).encode('utf-8')           # used to indicate there is zero payload
CONTROL_BYTE = chr(0x00).encode('utf-8')

# The minimum length of any packet, consists of a addresses, command and length byte
MIN_LENGTH = 12

#TODO: Convert 'utf-8' to a fixed variable

class Common:
    """
    This class contains methods that are used by both Hub and Node

    Not called independtly
    """

    def __init__(self):
        self.log = logging.getLogger()
        self.log.debug("[HDD] cls_CognIoTRF Common initialised")

        return


class Hub:
    """
    Provides the methods for Hub operation
    """
    def __init__(self, node, hub):
        # node and hub are normal strings passed in that are converted to binary mode
        self.log = logging.getLogger()
        self.log.debug("[HDD] cls_CognIoTRF HUB initialised")

        self.associated = False                 # USed to indicate if the Hub is associated
        self.node = node.encode('utf-8')        # The Node address that the instance supports
        self.hub = hub.encode('utf-8')          # The Hub address in use
        self.last_incoming_message = b''        # Set to the last valid packet
        self.log.info("[HDD]: HUB class instantiated with node:%s, hub:%s" % (self.node, self.hub))
        self._reset_values()
        #TODO: Track the time it is received
        return
        
    def decode_and_respond(self, message):
        # This method is for HUBS only
        # Taken the given message and process it.
        # Return the message to send
        # These are from the contents of the message, clear them all when processing the message 
        self._reset_values()
        self.hub_addr = b''         # The address of the hub in the message
        self.hub_control = b''      # The Control byte of the Hub in the message (future use)
        self.node_addr = b''        # The address of the node in the message
        self.node_control = b''     # The Control byte of the node in the message (future use)
        self.command = b''          # The command in the message
        self.payload_len = b''      # The length byte in the message
        self.payload = b''          # The payload in the message (optional)
                
        self.response = b''         # The message to be returned
        self.response_status = False    # The status of the responding message (True = Valid message)
        self.log.info("[HDD]: Message received for processing:%s" % message)
#TODO: Need to work through this again and check all covered!! - review other code

#TODO: respond with the message to send back and the status

        if self._split_message(message):
            self.time_packet_received = time.time()
            if self._validated():
                self.log.info("[HDD]: Message is valid ")
                if self.associated:
                    # Possible commands are data packet and ping (if associated)
                    self.log.info("[HDD]: HUB <==> NODE are associated")
                    if self.command == Ping:
                        # Send the Ping response
                        self.log.info("[HDD]: Ping Command Received")

                        #TODO: Need to include the ability to send data back in the ping response
                        self.response = self._generate_ack()
                        self.response_status = True
                    elif self.command == DataPacket:
                        # Send an Acknowledge
                        self.log.info("[HDD]: Data Packet Command Received")
                        if message == self.last_incoming_message:
                            self._display_message("RECV: Duplicate Packet Seen")
                            self.log.info("[HDD]: Duplicate Data Packet Received")
                        else:
                            self.last_incoming_message = message
                            self.response = self._generate_ack()
                            self.response_status = True
                    elif self.command == AssociationRequest:
                        # send Association Response again
                        self.log.info("[HDD]: Association Request Command Received")
                        self.response = self._association_response()
                        self.response_status = True
                    else:
                        self.log.info("[HDD]: Unknown Command Received")
                        self.response = self._generate_nack()
                        self.response_status = True
                else:
                    # Possible commands are association request
                    self.log.info("[HDD]: HUB & NODE are NOT associated")
                    if self.command == AssociationRequest:
                        # send Association Response
                        self.log.info("[HDD]: Association Request Command Received")
                        self.response = self._association_response()
                        self.response_status = True
                        # TODO: Need to do further checks before associated = True? maybe.
                        self.associated = True
            else:
                # Data is not valid
                self.log.info("[HDD]: Message received is invalid")
                self.response = b''
                self.response_status = False

    #TODO: Need to also deal with a failure in the LoRa comms, as maybe worth sending some other response.

        return
                
    def reply(self):
        # Return the response to send back
        return self.response
    
    def reply_status(self):
        # If True, a reply is to be sent
        return self.response_status

    def reply_payload_len(self):
        # The length of the data in the payload
        return int.from_bytes(self.payload_len, byteorder='big')
        
    def reply_payload(self):
        # The data that has been sent
        return self.payload
        
    def exit(self):
        # This routine is called to clean up any items on exit of the main program
        print("Bye!")
        
        return

#=======================================================================
#
#    P R I V A T E   F U N C T I O N S
#
#    Not to be Called Directly from outside class
#
#=======================================================================

    def _validated(self):
        # Routine to check the incoming packet is valid and for this instance of the NODE
            #TODO: Need to validate the packet, but what??
        if self.node != self.node_addr:
            self.log.info("[HDD]: Message Validation: Incorrect Node Address")
            return False
        elif self.hub != self.hub_addr:
            self.log.info("[HDD]: Message Validation: Incorrect Hub Address")
            return False
        elif self.hub_control != CONTROL_BYTE or self.node_control != CONTROL_BYTE:
            self.log.info("[HDD]: Message Validation: Incorrect Control Byte")
            return False
        elif len(self.payload) != int.from_bytes(self.payload_len, byteorder='big'):
            self.log.info("[HDD]: Message Validation: Incorrect Payload length byte doesn't match payload length")
            return False
        return True
    
    def _reset_values(self):
        # These are from the contents of the message, clear them all when processing the message 
        self.hub_addr = b''         # The address of the hub in the message
        self.hub_control = b''      # The Control byte of the Hub in the message (future use)
        self.node_addr = b''        # The address of the node in the message
        self.node_control = b''     # The Control byte of the node in the message (future use)
        self.command = b''          # The command in the message
        self.payload_len = b''      # The length byte in the message
        self.payload = b''          # The payload in the message (optional)
                
        self.response = b''         # The message to be returned
        self.response_status = False    # The status of the responding message (True = Valid message)

        return
    
    def _validate_packet(self, packet):
        
# TODO: This routine is not being used, but needs to be checked for tests to complete.

        # Take the given packet and validate it, return True if ok, False if not
        # checks for 5th and 10th bytes to be '!' or '>'
        # checks length to ba ta least 12 bytes
        # for if command is DataPacketandReq or DataPacketFinal then it can perform a CRC on the payload
        
        #TODO: Need to use the self.... parts, so need to split the 
    
        valid_packet = False         # assume packet is invalid
        if len(packet) >= MIN_LENGTH:                       # packet is long enough so continue
            if chr(packet[StartHubAddr+4]).encode('utf-8') == b'!' or chr(packet[StartHubAddr+4]).encode('utf-8') == b'>':
                # packet has valid 1st address descripters so continue
                if chr(packet[StartELBAddr+4]).encode('utf-8') == b'!' or chr(packet[StartELBAddr+4]).encode('utf-8') == b'>':
                    # 2nd addr descripter valid so continue
                    if chr(packet[StartCommand]).encode('utf-8') == DataPacketandReq or \
                            chr(packet[StartCommand]).encode('utf-8') == DataPacketFinal:
                                # now check payload
                       #ValidPacket = ValidatePayload(Packet) # Moved to log file writer
                       ValidPacket = True           # Validating of the payload moved to LogFileWriter
                    elif chr(packet[StartCommand]).encode('utf-8') == Ping or \
                                chr(packet[StartCommand]).encode('utf-8') == DataToSendReq:
                        # no payload so only addr descripters and message length can be used
                        valid_packet = True
        self.log.info("[HDD] - Packet of data has been validated :%s" % packet)
        return ValidPacket

    def _split_message(self, packet):
        # This routine takes the packet and splits it into its constituent parts
        # Returns True if successful, False if fails
        status = False
        if len(packet) >= MIN_LENGTH:
            self.hub_addr = packet[START_HUB_ADDR:HUB_CONTROL_BYTE]
            self.hub_control = chr(packet[HUB_CONTROL_BYTE]).encode('utf-8')
            self.node_addr = packet[START_NODE_ADDR:NODE_CONTROL_BYTE]
            self.node_control = chr(packet[NODE_CONTROL_BYTE]).encode('utf-8')
            self.command = chr(packet[COMMAND]).encode('utf-8')
            self.payload_len = chr(packet[PAYLOAD_LEN]).encode('utf-8')
            if len(packet) > PAYLOAD:
                # Onlyadd the payload if the length is longer than then minimum length
                self.payload = packet[PAYLOAD:]
            status = True
        self.log.debug("[HDD]: Hub Address    :%s" % self.hub_addr)
        self.log.debug("[HDD]: Node Address   :%s" % self.node_addr)
        self.log.debug("[HDD]: Command byte   :%s" % self.command)
        self.log.debug("[HDD]: Payload Length :%s" % self.payload_len)
        self.log.debug("[HDD]: Payload        :%s" % self.payload)
        return status
        
    def _association_response(self):
        # Create a generic generates an Ack for response to a number of messages
        packet_to_send = b''
        packet_to_send = packet_to_send + self.node_addr + self.node_control    # Receiver address & Control byte
        packet_to_send = packet_to_send + self.hub_addr + self.hub_control      # Sender address & Control byte
        packet_to_send = packet_to_send + AssociationResponse                   # Association Response
        packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

        self._display_message("SEND: Association Response")
        return packet_to_send
    
    def _generate_ack(self):
        # Create a generic generates an Ack for response to a number of messages
        packet_to_send = b''
        packet_to_send = packet_to_send + self.node_addr + self.node_control    # Receiver address & Control byte
        packet_to_send = packet_to_send + self.hub_addr + self.hub_control      # Sender address & Control byte
        packet_to_send = packet_to_send + ACK                                   # Acknowledge
        packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

        self._display_message("SEND: Acknowledge")
        return packet_to_send
    
    def _generate_nack(self):
        # Create a generic Nack for response to a number of messages
        # No additional decoding of Nack is completed.
        packet_to_send = b''
        packet_to_send = packet_to_send + self.node_addr + self.node_control    # Receiver address & Control byte
        packet_to_send = packet_to_send + self.hub_addr + self.hub_control      # Sender address & Control byte
        packet_to_send = packet_to_send + NACK                                  # Acknowledge
        packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

        self._display_message("SEND: Negative Response")
        return packet_to_send
    
    def _display_message(self, prompt):
        # Takes the current packet being processed and splits it onto the screen / log file
        #print("Message %s" % prompt)
        self.log.info("Message %s" % prompt)
        #print("Host:%s Hub:%s Node:%s CMD:%s LEN:%s PAY:%s\n" % (self.hub, self.hub_addr, self.node_addr, self.command, self.payload_len, self.payload))
        self.log.info("Host:%s Hub:%s Node:%s CMD:%s LEN:%s PAY:%s" % (self.hub, self.hub_addr, self.node_addr, self.command, self.payload_len, self.payload))
        return

class Node:
    """
    Provides the fmethods for the Node operation
    """
    
    def __init__(self, node, hub):
        # node and hub are normal strings passed in that are converted to binary mode
        self.log = logging.getLogger()
        self.log.debug("[HDD] cls_CognIoTRF NODE initialised")

        self.node = node.encode('utf-8')        # The Node address that the instance supports
        self.hub = hub.encode('utf-8')          # The Hub address in use
        self.log.info("[HDD]: NODE class instantiated with node:%s, hub:%s" % (self.node, self.hub))
        self.associated = False                # Associated is used to determine if the unit is already associated
        self._reset_values()
        #TODO: Track the time it is received
        return

    def data_to_send(self, data):
        # Pass in data to be sent when required
        # This doesn't send the data, use message_to_send for that
        self.data_to_send = data.encode('utf-8')
        return

#TODO: Need to tie this method with check_response


    def message_to_send(self):
        # Decide what message to send and return it
        # If no message to send, return an empty packet
        message = b''
        if self.associated == False:
            message = self._association_request()
        else:
            if len(self.data_to_send) > 0:
                # If there is data to send, send it
                message = self._data_packet(self.data_to_send)
                self.data_to_send = b''
            else:
                # If there is no data to send, send a ping
                #TODO: May need to only send ping sometimes, not everytime we loop round
                message = self._ping()
        return message

    def check_response(self, message):
        # After sending a message, check the response.
        # Return a status if it is successful
        if self._split_message(message):
            if self._validated():
                self.log.info("[HDD]: Message is valid ")
                if self.associated:
                    # Possible commands are data packet and ping (if associated)
                    self.log.info("[HDD]: HUB <==> NODE are associated")
                    if self.command == ACK:
                        # Received an Acknowledge
                        self.log.info("[HDD]: General Acknowledge received")
                        self.response_status = True
                    elif self.command == NACK:
                        # Received a Not Acknowledged
                        self.log.info("[HDD]: Not Acknowledged Command Received")
                        self.response_status = False
                    else:
                        self.log.info("[HDD]: Unknown Command Received")
                        self.response_status = False
                else:
                    # Possible commands are association request
                    self.log.info("[HDD]: HUB & NODE are NOT associated")
                    if self.command == AssociationResponse:
                        # Received an Associated Response
                        self.log.info("[HDD]: Assocation Response Command Received")
                        self.associated = True
                        self.response_status = True
            else:
                # Data is not valid
                self.log.info("[HDD]: Message received is invalid")
                self.response_status = False
        return self.response_status

    #TODO: Need to also deal with a failure in the LoRa comms, as maybe worth sending some other response.


    


#=======================================================================
#
#    P R I V A T E   F U N C T I O N S
#
#    Not to be Called Directly from outside class
#
#=======================================================================

    def _reset_values(self):
        # These are from the contents of the message, clear them all when processing the message 
        self.hub_addr = b''         # The address of the hub in the message
        self.hub_control = b''      # The Control byte of the Hub in the message (future use)
        self.node_addr = b''        # The address of the node in the message
        self.node_control = b''     # The Control byte of the node in the message (future use)
        self.command = b''          # The command in the message
        self.payload_len = b''      # The length byte in the message
        self.payload = b''          # The payload in the message (optional)
        self.data_to_send = b''     # The data to be managed and sent
        self.response = b''         # The message to be returned
        self.response_status = False    # The status of the responding message (True = Valid message)
        self.outgoing_message = b''     # The message to be transmitted

        return

    def _association_request(self):
        # Prepare an Associate message to send
        # return the message to be sent
        #TODO: Hub becomes receiver HUB - RECEIVER
        #TODO: Node becomes sender  NODE - SENDER

        packet_to_send = b''
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + AssociationRequest
        packet_to_send = packet_to_send + ZeroPayload
        return packet_to_send

    def _data_packet(self, data):
        # Prepare a Data Packet message with the included data supplied
        # Data is supplied as a string
        # return the message to be sent

        # build the packet here using things like
        #self.hub, self.node, CONTROL_BYTE, 
        #TODO: Hub becomes receiver HUB - RECEIVER
        #TODO: Node becomes sender  NODE - SENDER
        packet_to_send = b''
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + DataPacket
        packet_to_send = packet_to_send + str(len(data)).encode('utf-8')
        packet_to_send = packet_to_send + data.encode('utf-8')
        return packet_to_send

    def _ping(self):
        # Prepare a Data Packet message to send the ping
        # return the message to be sent
        # build the packet here using things like
        #TODO: Hub becomes receiver HUB - RECEIVER
        #TODO: Node becomes sender  NODE - SENDER
        packet_to_send = b''
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + Ping
        packet_to_send = packet_to_send + ZeroPayload

        packet_to_send       # contains the message to be sent back
        return packet_to_send

