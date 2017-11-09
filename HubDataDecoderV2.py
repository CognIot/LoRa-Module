'''
Hub Data Decoder

An instance of the NODE class is created for each Node <==> Hub association

#TODO: Complete testing
#TODO: Add in capability for multiple nodes to work with the one hub.
    Something to be added into validated after the item has been associated.
    
#TODO: Hub becomes receiver HUB -> RECEIVER
#TODO: Node becomes sender  NODE -> SENDER
'''
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

class NODE:
    '''
    Class to handle all the processing of messages from the Node
    
    No need for timeout as there are no sequenced comms, only ping, association and send data
    '''
    def __init__(self, node, hub):
        # node and hub are normal strings passed in that are converted to binary mode
        
        self.associated = False                 # Associated is used to determine if the unit is already associated
        self.node = node.encode('utf-8')        # The Node address that the instance supports
        self.hub = hub.encode('utf-8')          # The Hub address in use
        self.last_incoming_message = b''        # Set to the last valid packet
        logging.info("[HDD]: NODE class instantiated with node:%s, hub:%s" % (self.node, self.hub))
        self._reset_values()
        #TODO: Track the time it is received
        return
        
    #TODO: Should incoming reply with something, maybe the status?
    def incoming(self, message):
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
        logging.info("[HDD]: Message received for processing:%s" % message)
#TODO: Need to work through this again and check all covered!! - review other code


        if self._split_message(message):
            self.time_packet_received = time.time()
            if self._validated():
                logging.info("[HDD]: Message is valid ")
                if self.associated:
                    # Possible commands are data packet and ping (if associated)
                    logging.info("[HDD]: HUB <==> NODE are associated")
                    if self.command == Ping:
                        # Send the Ping response
                        logging.info("[HDD]: Ping Command Received")

                        #TODO: Need to include the ability to send data back in the ping response
                        self.response = self._generate_ack()
                        self.response_status = True
                    elif self.command == DataPacket:
                        # Send an Acknowledge
                        logging.info("[HDD]: Data Packet Command Received")
                        if message == self.last_incoming_message:
                            self._display_message("RECV: Duplicate Packet Seen")
                            logging.info("[HDD]: Duplicate Data Packet Received")
                        else:
                            self.last_incoming_message = message
                            self.response = self._generate_ack()
                            self.response_status = True
                    elif self.command == AssociationRequest:
                        # send Association Response again
                        logging.info("[HDD]: Association Request Command Received")
                        self.response = self._association_response()
                        self.response_status = True
                    else:
                        logging.info("[HDD]: Unknown Command Received")
                        self.response = self._generate_nack()
                        self.response_status = True
                else:
                    # Possible commands are association request
                    logging.info("[HDD]: HUB & NODE are NOT associated")
                    if self.command == AssociationRequest:
                        # send Association Response
                        logging.info("[HDD]: Association Request Command Received")
                        self.response = self._association_response()
                        self.response_status = True
                        # TODO: Need to do further checks before associated = True? maybe.
                        self.associated = True
            else:
                # Data is not valid
                logging.info("[HDD]: Message received is invalid")
                self.response = b''
                self.response_status = False
    #TODO: Do we send unrecognised command

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


#TODO: Methods to create
    def outgoing_AssociateRequest(self):
        # Prepare an Associate message to send
        # return the message to be sent
        #TODO: Hub becomes receiver HUB - RECEIVER
        #TODO: Node becomes sender  NODE - SENDER

        self.outgoing_message = b''
        self.outgoing_message = self.outgoing_message + self.hub + CONTROL_BYTE      # Sender address & Control byte
        self.outgoing_message = self.outgoing_message + self.node + CONTROL_BYTE    # Receiver address & Control byte
        self.outgoing_message = self.outgoing_message + AssociationRequest
        self.outgoing_message = self.outgoing_message + ZeroPayload
        return self.outgoing_message

    def outgoing_DataPack(self, data):
        # Prepare a Data Packet message with the included data supplied
        # Data is supplied as a string
        # return the message to be sent

        # build the packet here using things like
        #self.hub, self.node, CONTROL_BYTE, 
        #TODO: Hub becomes receiver HUB - RECEIVER
        #TODO: Node becomes sender  NODE - SENDER
        self.outgoing_message = b''
        self.outgoing_message = self.outgoing_message + self.hub + CONTROL_BYTE      # Sender address & Control byte
        self.outgoing_message = self.outgoing_message + self.node + CONTROL_BYTE    # Receiver address & Control byte
        self.outgoing_message = self.outgoing_message + DataPacket
        self.outgoing_message = self.outgoing_message + chr(data).encode('utf-8')
        self.outgoing_message = self.outgoing_message + data.encode('utf-8')
        return self.outgoing_message

    def outgoing_Ping(self):
        # Prepare a Data Packet message to send the ping
        # return the message to be sent
        # build the packet here using things like
        #TODO: Hub becomes receiver HUB - RECEIVER
        #TODO: Node becomes sender  NODE - SENDER
        self.outgoing_message = b''
        self.outgoing_message = self.outgoing_message + self.hub + CONTROL_BYTE      # Sender address & Control byte
        self.outgoing_message = self.outgoing_message + self.node + CONTROL_BYTE    # Receiver address & Control byte
        self.outgoing_message = self.outgoing_message + Ping
        self.outgoing_message = self.outgoing_message + ZeroPayload

        self.outgoing_message       # contains the message to be sent back
        return self.outgoing_message

    
    def exit_hub(self):
        # This routine is called to clean up any items on exit of the main program
        print("Bye!")
        
        return

#-----------------------------------------------------------------------------------------------------------------------
# Routines below here are for internal use only
    
    def _validated(self):
        # Routine to check the incoming packet is valid and for this instance of the NODE
            #TODO: Need to validate the packet, but what??
        if self.node != self.node_addr:
            logging.info("[HDD]: Message Validation: Incorrect Node Address")
            return False
        elif self.hub != self.hub_addr:
            logging.info("[HDD]: Message Validation: Incorrect Hub Address")
            return False
        elif self.hub_control != CONTROL_BYTE or self.node_control != CONTROL_BYTE:
            logging.info("[HDD]: Message Validation: Incorrect Control Byte")
            return False
        elif len(self.payload) != int.from_bytes(self.payload_len, byteorder='big'):
            logging.info("[HDD]: Message Validation: Incorrect Payload length byte doesn't match payload length")
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

        self.outgoing_message = b''     # The message to be transmitted
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
        logging.info("[HDD] - Packet of data has been validated :%s" % packet)
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
        logging.debug("[HDD]: Hub Address    :%s" % self.hub_addr)
        logging.debug("[HDD]: Node Address   :%s" % self.node_addr)
        logging.debug("[HDD]: Command byte   :%s" % self.command)
        logging.debug("[HDD]: Payload Length :%s" % self.payload_len)
        logging.debug("[HDD]: Payload        :%s" % self.payload)
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
        logging.info("Message %s" % prompt)
        #print("Host:%s Hub:%s Node:%s CMD:%s LEN:%s PAY:%s\n" % (self.hub, self.hub_addr, self.node_addr, self.command, self.payload_len, self.payload))
        logging.info("Host:%s Hub:%s Node:%s CMD:%s LEN:%s PAY:%s" % (self.hub, self.hub_addr, self.node_addr, self.command, self.payload_len, self.payload))
        return


