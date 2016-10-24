#!/usr/bin/env python3
'''

#TODO:
Implement all test scenarios.

This program is used to test the HubDataDecovderV2 program

Test Scenarios left to complete:

Duplicate Packet
Wrong Control byte
Missing Control byte
    
Random Data


'''

import sys
import logging

import HubDataDecoderV2 as HT_Hub

# Pointers to the position of the parts of the packet
HT_START_HUB_ADDR = 0          # Position in packet where hub address starts
HT_START_NODE_ADDR = 5         # Position in packet where node starts
HT_COMMAND = 10                # Position in packet where the command byte is
HT_PAYLOAD_LEN = 11            # Position in packet where the payload length byte is
HT_PAYLOAD = 12                # Position in packet where the payload starts


# Constants that will not change in program
# Command bytes that are used by protocol
HT_ASSC_REQ = chr(0x30).encode('utf-8')
HT_ASSC_RSP = chr(0x31).encode('utf-8')
HT_DATA_PKT = chr(0x37).encode('utf-8')
HT_PING = chr(0x32).encode('utf-8')

HT_CONTROL_BYTE = chr(0x00).encode('utf-8')      # The Control byte
HT_ZERO_PAYLOAD = chr(0x00).encode('utf-8')           # used to indicate there is zero payload


# Response codes
HT_ACK = chr(0x22).encode('utf-8')                 # all good and confirmed
HT_NACK = chr(0x99).encode('utf-8')                # General NACK response

def ht_association(test, hub, node, assc=True):
    # Build the Association Request Command
    packet_to_send = hub + HT_CONTROL_BYTE + node + HT_CONTROL_BYTE + HT_ASSC_REQ + HT_ZERO_PAYLOAD
    if assc == True:
        packet_to_check = node + HT_CONTROL_BYTE + hub + HT_CONTROL_BYTE + HT_ASSC_RSP + HT_ZERO_PAYLOAD
        packet_status = True
    else:
        packet_to_check = b''
        packet_status = False
    return [test, packet_to_send, packet_to_check, packet_status, b'']

def ht_ping(test, hub, node, assc=True):
    # Build the Association Request Command
    packet_to_send = hub + HT_CONTROL_BYTE + node + HT_CONTROL_BYTE + HT_PING + HT_ZERO_PAYLOAD
    if assc == True:
        packet_to_check = node + HT_CONTROL_BYTE + hub + HT_CONTROL_BYTE + HT_ACK + HT_ZERO_PAYLOAD
        packet_status = True
    else:
        # Ping doesn't respond if the Hub and Module are not associated
        packet_to_check = b''
        packet_status = False
    return [test, packet_to_send, packet_to_check, packet_status, b'']

def generate_payload(size):
    # Generate the payload of the given size, max is 127 characters
    ht_payload = ''
    for byte in range(0,256):
        ht_payload = ht_payload + chr(byte)

    ht_payload = ht_payload[0:size].encode('utf-8')
    return ht_payload
    
def ht_receive_data(test, hub, node, data_len, assc=True):
    # Build the Association Request Command
    packet_payload = generate_payload(data_len)
    packet_to_send = hub + HT_CONTROL_BYTE + node + HT_CONTROL_BYTE + HT_DATA_PKT + chr(data_len).encode('utf-8') + packet_payload
    if assc == True:
        packet_to_check = node + HT_CONTROL_BYTE + hub + HT_CONTROL_BYTE + HT_ACK + HT_ZERO_PAYLOAD
        packet_status = True
    else:
        # Receive Data doesn't respond if the Hub and Module are not associated
        packet_to_check = b''
        packet_status = False
    return [test, packet_to_send, packet_to_check, packet_status, packet_payload]
    
def ht_receive_data_dup(test, hub, node, data_len, assc=True):
    # Build the Association Request Command for a duplicate set of data
    # Make the length byte the same as the previous one
    packet_payload = generate_payload(data_len)
    packet_to_send = hub + HT_CONTROL_BYTE + node + HT_CONTROL_BYTE + HT_DATA_PKT + chr(data_len).encode('utf-8') + packet_payload
    packet_to_check = b''
    packet_status = False
    return [test, packet_to_send, packet_to_check, packet_status, packet_payload]
    
def ht_receive_data_bad(test, hub, node, exp_len, act_len, assc=True):
    # Build the Association Request Command
    packet_payload = generate_payload(act_len)
    packet_to_send = hub + HT_CONTROL_BYTE + node + HT_CONTROL_BYTE + HT_DATA_PKT + chr(exp_len).encode('utf-8') + packet_payload
    if assc == True:
        packet_to_check = node + HT_CONTROL_BYTE + hub + HT_CONTROL_BYTE + HT_NACK + HT_ZERO_PAYLOAD
        packet_status = True
    else:
        # Receive Data doesn't respond if the Hub and Module are not associated
        packet_to_check = b''
        packet_status = False
    return [test, packet_to_send, packet_to_check, packet_status, packet_payload]
    
def build_scenarios(bs_node):
    # Build the required scenarios with a positive response and return them as a dictionary
    # e.g. scenario {b'1234!0000!2\x00':b'0000!1234!"\x00'}
    # List of messages includes additional PIngs and Data Packs for the good unit
    # Associated components
    bs_hub = b'ABCD'
    # Non associated addresses
    na_hub = b'FFFF'
    na_node = b'9999'

    build = []
    # Non Associated
    build.append(ht_ping("Ping outside Associate", bs_hub, bs_node, False))               #   Ping outside Associate, hence False
    build.append(ht_receive_data("Received Data Outside Associate",bs_hub, bs_node, 21, False))   #   ReceiveData Outside Associate, hence False
    # Good Day
    build.append(ht_association("Association Req", bs_hub, bs_node))               #   Association
    build.append(ht_association("2nd Association Request", bs_hub, bs_node))               #   Associate Twice
    build.append(ht_ping("Normal Ping", bs_hub, bs_node))                      #   Ping
    build.append(ht_receive_data("Normal Sending of data 1", bs_hub, bs_node, 1))           #   ReceiveData
    build.append(ht_receive_data("Normal Sending of data 2", bs_hub, bs_node, 16))          #   ReceiveData
    build.append(ht_receive_data("Normal Sending of data 3", bs_hub, bs_node, 56))          #   ReceiveData
    build.append(ht_ping("Normal Ping", bs_hub, bs_node))                      #   Ping
    build.append(ht_receive_data("Normal Sending of data 4", bs_hub, bs_node, 82))          #   ReceiveData
    build.append(ht_receive_data("Normal Sending of data 5", bs_hub, bs_node, 127))         #   ReceiveData         **** What is the maximum length

    # Good Day but with wrong Hub address - there should be no responses.
    build.append(ht_association("Wrong Hub Association Req", na_hub, bs_node, False))        #   Association
    build.append(ht_ping("Normal Ping", bs_hub, bs_node))                      #   Ping
    build.append(ht_association("Wrong Hub 2nd Assocation Req", na_hub, bs_node, False))        #   Associate Twice
    build.append(ht_ping("Wrong Hub Sending Ping", na_hub, bs_node, False))               #   Ping
    build.append(ht_receive_data("Normal Sending of data 5 Duplicate", bs_hub, bs_node, 127, False))   # ReceiveData same length as before to force duplicate
    build.append(ht_receive_data("Wrong Hub Sending of data 1", na_hub, bs_node, 16, False))   #   ReceiveData
    build.append(ht_ping("Normal Ping", bs_hub, bs_node))                      #   Ping
    build.append(ht_receive_data("Wrong Hub Sending of data 2", na_hub, bs_node, 56, False))   #   ReceiveData
    build.append(ht_ping("Wrong Hub Sending Ping", na_hub, bs_node, False))               #   Ping
    build.append(ht_receive_data("Normal Sending of data 7", bs_hub, bs_node, 56))         # Same length as previous send message, but different Node so should be ok.
    build.append(ht_receive_data("Wrong Hub Sending of data 3", na_hub, bs_node, 82, False))   #   ReceiveData
    
    # Good Day but with wrong Node address - there should be no responses.
    build.append(ht_association("Wrong Node Address in Association", bs_hub, na_node, False))        #   Association
    build.append(ht_ping("Normal Ping", bs_hub, bs_node))                      #   Ping
    build.append(ht_receive_data("Normal Sending of data 8", bs_hub, bs_node, 17))         #   ReceiveData         **** What is the maximum length
    build.append(ht_association("Wrong Node Address in 2nd Association", bs_hub, na_node, False))        #   Associate Twice
    build.append(ht_ping("Wrong Node Address in Ping", bs_hub, na_node, False))               #   Ping
    build.append(ht_receive_data("Wrong Node Address in Sending Data 1", bs_hub, na_node, 14, False))   #   ReceiveData
    build.append(ht_receive_data("Normal Sending of data 9", bs_hub, bs_node, 84))         #   ReceiveData         **** What is the maximum length
    build.append(ht_receive_data("Wrong Node Address in Sending Data 2", bs_hub, na_node, 37, False))   #   ReceiveData
    build.append(ht_ping("Normal Ping", bs_hub, bs_node))                      #   Ping
    build.append(ht_ping("Wrong Node Address in Ping", bs_hub, na_node, False))               #   Ping
    build.append(ht_receive_data("Wrong Node Address in Sending Data 3", bs_hub, na_node, 61, False))   #   ReceiveData
    build.append(ht_receive_data("Normal Sending of data 10", bs_hub, bs_node, 63))         #   ReceiveData         **** What is the maximum length

    # Associated but with wrong data payloads
    for length in range(0,14):
        build.append(ht_receive_data_bad("Sending Data - payload too short %s" % length, bs_hub, bs_node, 14, length, False))   #   Good Day but with message length too short by 1 - 12 bytes
    for length in range(15,24):
        build.append(ht_receive_data_bad("Sending Data - payload too long "+str(length), bs_hub, bs_node, 14, length, False))       #   Good Day but with message length too long by 1 - 10 bytes
    build.append(ht_receive_data_bad("Sending Data - NO payload", bs_hub, na_node, 5, 0, False))             #   ReceiveData but with no payload

    return build

def ht_main():
    # The main program that calls all the necessary routines to test the HubDataDecoderV2.py
    node_list = []
    node_list = [b'1234', b'2345', b'3456', b'4567', b'5678', b'6789', b'7890']
    scenarios = {}
    nodes = {}

    # Build a list of nodes and associated scenarios
    for node in node_list:
        instance = HT_Hub.NODE(node, b'ABCD')
        nodes.update({node: instance})
        node_scenarios = build_scenarios(node)
        scenarios.update({node:node_scenarios})

    for msg_no in range(0,len(node_scenarios)):
        for node_no in range(0,len(node_list)):
            scenario = scenarios[node_list[node_no]]
            msg = scenario[msg_no]
            nodes[node_list[node_no]].incoming(msg[1])
            if msg[2] == nodes[node_list[node_no]].reply() and msg[3] == nodes[node_list[node_no]].reply_status():
                print(".", end="", flush=True)
            else:
                print("\n%s Test FAILED!!!!!" % msg[0])
                print("Send:>%s<, receive >%s<, status>%s<" % (msg[1], msg[2], msg[3]))
                print("     Response: %s" % nodes[node_list[node_no]].reply())
                print("     Response Status: %s" % nodes[node_list[node_no]].reply_status())
    print("\nMessage:%s, Nodes:%s" % (msg_no, node_no))
    return






# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    logging.basicConfig(filename="Hub_Test.txt", filemode="w", level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(message)s')

    try:
        ht_main()
    
    except:
        # This won't work as it requires knowledge of the instances
        Hub.exit_comms()
        print("Program Ended...")
        sys.exit()
