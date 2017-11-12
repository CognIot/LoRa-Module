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
START_DEST_ADDR = 0         # Position in packet where hub address starts
DEST_CONTROL_BYTE = 4       # Position of the Hub Control byte
START_SRC_ADDR = 5          # Position in packet where node starts
SRC_CONTROL_BYTE = 9        # Position of the Node Control byte
COMMAND = 10                # Position in packet where the command byte is
PAYLOAD_LEN = 11            # Position in packet where the payload length byte is
PAYLOAD = 12                # Position in packet where the payload starts


#TODO: Change all these to all capitals with underscores

# Constants that will not change in program
# Command bytes that are used by protocol
ASSOCIATIONREQUEST = chr(0x30).encode('utf-8')
ASSOCIATIONRESPONSE = chr(0x31).encode('utf-8')
DATAPACKET = chr(0x37).encode('utf-8')
PING = chr(0x32).encode('utf-8')

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
    def __init__(self, hub, node):
        # node and hub are normal strings passed in that are converted to binary mode
        self.log = logging.getLogger()
        self.log.debug("[HDD] cls_CognIoTRF HUB initialised")

        self.associated = False                 # USed to indicate if the Hub is associated
        self.node = node.encode('utf-8')        # The Node address that the instance supports
        self.hub = hub.encode('utf-8')          # The Hub address in use
        self.last_incoming_message = b''        # Set to the last valid packet
        self.log.info("[HDD]: HUB class instantiated with node:%s, hub:%s" % (self.node, self.hub))
        self._reset_values()
        return
        
    def decode_and_respond(self, message):
        # This method is for HUBS only
        # Taken the given message and process it.
        # Return the message to send
        # These are from the contents of the message, clear them all when processing the message 
        self._reset_values()
                
        self.log.info("[HDD]: Message received for processing:%s" % message)

        if self._split_message(message):
            self.time_packet_received = time.time()
            if self._validated():
                self.log.info("[HDD]: Message is valid ")
                if self.associated:
                    # Possible commands are data packet and ping (if associated)
                    self.log.info("[HDD]: HUB <==> NODE are associated")
                    if self.command == PING:
                        # Send the Ping response
                        self.log.info("[HDD]: Ping Command Received")

                        #TODO: Need to include the ability to send data back in the ping response
                        self.response = self._generate_ack()
                        self.response_status = True
                    elif self.command == DATAPACKET:
                        # Send an Acknowledge
                        self.log.info("[HDD]: Data Packet Command Received")
                        if message == self.last_incoming_message:
                            self._display_message("RECV: Duplicate Packet Seen")
                            self.log.info("[HDD]: Duplicate Data Packet Received")
                        else:
                            self.last_incoming_message = message
                            self.response = self._generate_ack()
                            self.response_status = True
                    elif self.command == ASSOCIATIONREQUEST:
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
                    if self.command == ASSOCIATIONREQUEST:
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
        # Routine to check the incoming packet TO the HUB is valid from the node
        if self.hub != self.dest_addr:
            self.log.info("[HDD]: Message Validation: Incorrect Destination Address, doesn't match hub")
            return False
        elif self.node != self.src_addr:
            self.log.info("[HDD]: Message Validation: Incorrect Source Address, doesn't match node")
            return False
        elif self.src_control != CONTROL_BYTE or self.dest_control != CONTROL_BYTE:
            self.log.info("[HDD]: Message Validation: Incorrect Control Byte")
            return False
        elif len(self.payload) != int.from_bytes(self.payload_len, byteorder='big'):
            self.log.info("[HDD]: Message Validation: Incorrect Payload length byte doesn't match payload length")
            return False
        return True
    
    def _reset_values(self):
        # These are from the contents of the message, clear them all when processing the message 
        self.dest_addr = b''        # The address of the hub in the message
        self.dest_control = b''     # The Control byte of the Hub in the message (future use)
        self.src_addr = b''         # The address of the node in the message
        self.src_control = b''      # The Control byte of the node in the message (future use)
        self.command = b''          # The command in the message
        self.payload_len = b''      # The length byte in the message
        self.payload = b''          # The payload in the message (optional)
                
        self.response = b''         # The message to be returned
        self.response_status = False    # The status of the responding message (True = Valid message)

        return

    def _split_message(self, packet):
        # This routine takes the packet and splits it into its constituent parts
        # Returns True if successful, False if fails
        status = False
        if len(packet) >= MIN_LENGTH:
            self.dest_addr = packet[START_DEST_ADDR:DEST_CONTROL_BYTE]
            self.dest_control = chr(packet[DEST_CONTROL_BYTE]).encode('utf-8')
            self.src_addr = packet[START_SRC_ADDR:SRC_CONTROL_BYTE]
            self.src_control = chr(packet[SRC_CONTROL_BYTE]).encode('utf-8')
            self.command = chr(packet[COMMAND]).encode('utf-8')
            self.payload_len = chr(packet[PAYLOAD_LEN]).encode('utf-8')
            if len(packet) > PAYLOAD:
                # Onlyadd the payload if the length is longer than then minimum length
                self.payload = packet[PAYLOAD:]
            status = True
        self.log.debug("[HDD]: Destination Address  :%s" % self.dest_addr)
        self.log.debug("[HDD]: Source Address       :%s" % self.src_addr)
        self.log.debug("[HDD]: Command byte         :%s" % self.command)
        self.log.debug("[HDD]: Payload Length       :%s" % self.payload_len)
        self.log.debug("[HDD]: Payload              :%s" % self.payload)
        return status
        
    def _association_response(self):
        # Create a generic generates an Ack for response to a number of messages
        packet_to_send = b''
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + ASSOCIATIONRESPONSE                   # Association Response
        packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

        self._display_message("SEND: Association Response")
        return packet_to_send
    
    def _generate_ack(self):
        # Create a generic generates an Ack for response to a number of messages
        packet_to_send = b''
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + ACK                                   # Acknowledge
        packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

        self._display_message("SEND: Acknowledge")
        return packet_to_send
    
    def _generate_nack(self):
        # Create a generic Nack for response to a number of messages
        # No additional decoding of Nack is completed.
        packet_to_send = b''
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + NACK                                  # Acknowledge
        packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

        self._display_message("SEND: Negative Response")
        return packet_to_send
    
    def _display_message(self, prompt):
        # Takes the current packet being processed and splits it onto the screen / log file
        #print("Message %s" % prompt)
        self.log.info("Message %s" % prompt)
        #print("Host:%s Hub:%s Node:%s CMD:%s LEN:%s PAY:%s\n" % (self.hub, self.hub_addr, self.node_addr, self.command, self.payload_len, self.payload))
        self.log.info("Host:%s Dest:%s Src:%s CMD:%s LEN:%s PAY:%s" % (self.hub, self.dest_addr, self.src_addr, self.command, self.payload_len, self.payload))
        return

class Node:
    """
    Provides the fmethods for the Node operation

    Message  Structure
        Bytes  - Meaning
        ====== - =======
        0 - 3  - Destination
        4      - Destination Control
        5 - 8  - Source
        9      - Source Control
        10     - Command Byte
        11     - Payload Length
        12 - n - Payload
    
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

    def set_data_to_be_sent(self, data):
        # Pass in data to be sent when required
        # This doesn't send the data, use message_to_send for that
        self.data_to_send = data.encode('utf-8')
        self.data_sent = True
        return

    def read_data_sent_status(self):
        # Return the current buffer of the data to be sent
        return self.data_sent

    def force_reassociation(self):
        # This will force the message to re-assocaite
        self.assocaited = False
        return
        
#TODO: Need to tie this method with check_response
    def message_to_send(self):
        # Decide what message to send and return it
        # If no message to send, return an empty packet
        message = b''
        if self.associated == False:
            message = self._association_request()
            self.data_sent = False
        else:
            if len(self.data_to_send) > 0:
                # If there is data to send, send it
                message = self._data_packet(self.data_to_send)
                self.data_to_send = b''
                self.data_sent = True
            else:
                # If there is no data to send, send a ping
                #TODO: May need to only send ping sometimes, not everytime we loop round
                message = self._ping()
                self.data_sent = False
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
                    if self.command == ASSOCIATIONRESPONSE:
                        # Received an Associated Response
                        self.log.info("[HDD]: Assocation Response Command Received")
                        self.associated = True
                        self.response_status = True
                    else:
                        self.log.ingfo("[HDD] Message received not association response for a non assocaited Node")
                        self.associated = False
                        self.response_status = False
            else:
                # Data is not valid
                self.log.info("[HDD]: Message received is invalid")
                self.response_status = False
        else:
            # Unable to Decode the message
            self.log.info("[HDD]: Unable to Decode the message, message is invalid")
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

    def _validated(self):
        # Routine to check the incoming packet TO the Node is valid
        if self.node != self.dest_addr:
            self.log.info("[HDD]: Message Validation: Incorrect Destination Address, doesn't match Node")
            return False
        elif self.hub != self.src_addr:
            self.log.info("[HDD]: Message Validation: Incorrect Source Address, doesn't match Hub")
            return False
        elif self.dest_control != CONTROL_BYTE or self.src_control != CONTROL_BYTE:
            self.log.info("[HDD]: Message Validation: Incorrect Control Byte")
            return False
        return True

    def _split_message(self, packet):
        # This routine takes the incoming packet and splits it into its constituent parts
        # Returns True if successful, False if fails
        """
        0 - 3  - Destination
        4      - Destination Control
        5 - 8  - Source
        9      - Source Control
        10     - Command Byte
        11     - Payload Length
        12 - n - Payload
        """
        status = False
        if len(packet) >= MIN_LENGTH:
            self.dest_addr = packet[START_DEST_ADDR:DEST_CONTROL_BYTE]
            self.dest_control = chr(packet[DEST_CONTROL_BYTE]).encode('utf-8')
            self.src_addr = packet[START_SRC_ADDR:SRC_CONTROL_BYTE]
            self.src_control = chr(packet[SRC_CONTROL_BYTE]).encode('utf-8')
            self.command = chr(packet[COMMAND]).encode('utf-8')
            self.payload_len = chr(packet[PAYLOAD_LEN]).encode('utf-8')
            if len(packet) > PAYLOAD:
                # Onlyadd the payload if the length is longer than then minimum length
                self.payload = packet[PAYLOAD:]
            status = True
        self.log.debug("[HDD]: Destination Address  :%s" % self.dest_addr)
        self.log.debug("[HDD]: Source Address       :%s" % self.src_addr)
        self.log.debug("[HDD]: Command byte         :%s" % self.command)
        self.log.debug("[HDD]: Payload Length       :%s" % self.payload_len)
        self.log.debug("[HDD]: Payload              :%s" % self.payload)
        return status
        
    def _reset_values(self):
        # These are from the contents of the message, clear them all when processing the message 
        self.dest_addr = b''         # The address of the hub in the message
        self.dest_control = b''      # The Control byte of the Hub in the message (future use)
        self.src_addr = b''        # The address of the node in the message
        self.src_control = b''     # The Control byte of the node in the message (future use)
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

        packet_to_send = b''
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + ASSOCIATIONREQUEST
        packet_to_send = packet_to_send + ZeroPayload
        self.log.debug("[HDD] Assocation Request Message:%s" % packet_to_send)
        return packet_to_send

    def _data_packet(self, data):
        # Prepare a Data Packet message with the included data supplied
        # Data is supplied as a string
        # return the message to be sent

        packet_to_send = b''
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + DATAPACKET
        packet_to_send = packet_to_send + str(len(data)).encode('utf-8')
        packet_to_send = packet_to_send + data
        self.log.debug("[HDD] Data Packet Message:%s" % packet_to_send)
        return packet_to_send

    def _ping(self):
        # Prepare a Data Packet message to send the ping
        # return the message to be sent

        packet_to_send = b''
        packet_to_send = packet_to_send + self.hub + CONTROL_BYTE      # Sender address & Control byte
        packet_to_send = packet_to_send + self.node + CONTROL_BYTE    # Receiver address & Control byte
        packet_to_send = packet_to_send + PING
        packet_to_send = packet_to_send + ZeroPayload
        self.log.debug("[HDD] Ping Message:%s" % packet_to_send)
        packet_to_send       # contains the message to be sent back
        return packet_to_send

