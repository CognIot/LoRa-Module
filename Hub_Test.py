#!/usr/bin/env python3
'''

#TODO:
Implement all test scenarios.

This program is used to test the HubDataDecovderV2 program

Test Scenarios:

Good Day
    Association
    Ping
    ReceiveData
    ReceiveData
    Ping
    ReceiveData

Non Associated
    Ping outside Associate
    ReceiveData Outrside Associate
    Associate Twice

Good Day but with wrong Node address
Good Day but with wrong Hub address

Good Day but with message length too short by 1 - 12 bytes
Good Day but with message length too long by 1 - 10 bytes
ReceiveData but with no payload
ReceiveData but with wrong payload length byte, too short and too long

Wrong exec byte
Missing Exec byte

Random Data

Single node, single hub
Multiple nodes, single Hub
Multiple nodes, multiple Hubs

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

HT_EXECBYTE = "!".encode('utf-8')      # The executive by
HT_ZERO_PAYLOAD = chr(0x00).encode('utf-8')           # used to indicate there is zero payload


# Response codes
HT_ACK = chr(0x22).encode('utf-8')                 # all good and confirmed
HT_NACK = chr(0x99).encode('utf-8')                # General NACK response

def ht_association(hub, node):
    # Build the Association Request Command
    packet_to_send = hub + HT_EXECBYTE + node + HT_EXECBYTE + HT_ASSC_REQ + HT_ZERO_PAYLOAD
    packet_to_check = node + HT_EXECBYTE + hub + HT_EXECBYTE + HT_ASSC_RSP + HT_ZERO_PAYLOAD
    packet_status = True
    return [packet_to_send, packet_to_check, packet_status]

    
def build_scenarios():
    # Build the required scenarios with a positive response and return them as a dictionary
    # e.g. scenario {b'1234!0000!2\x00':b'0000!1234!"\x00'}
    #Good Day
    bs_hub = b'0000'
    bs_node = b'1234'
    build = []
    build.append(ht_association(bs_hub, bs_node))
#        Association
#        Ping
#        ReceiveData
#        ReceiveData
#        Ping
#        ReceiveData
    return build

def ht_main():
    # The main program that calls all the necessary routines to tes tthe HubDataDecoderV2.py
    
    nodes = {}
    instance = HT_Hub.NODE(b'1234!', b'0000!')
    nodes.update({b'1234!': instance})
    
    scenarios = []
    scenarios = build_scenarios()
    for msg in scenarios:
        print("Send:>%s<, receive >%s<, status>%s<" % (msg[0], msg[1], msg[2]))
        nodes[b'1234!'].incoming(msg[0])
        if msg[1] == nodes[b'1234!'].reply() and msg[2] == nodes[b'1234!'].reply_status():
            print("Test PASSED")
        else:
            print("Test FAILED!!!!!")
            print("     Response: %s" % nodes[b'1234!'].reply())
            print("     Response Status: %s" % nodes[b'1234!'].reply_status())
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
