#!/usr/bin/env python3
"""
This program is used to control the communications between the Hub and the Node


"""

import sys

import LoRaCommsReceiverV2 as LoRa
import HubDataDecoderV2 as Hub





def main():
    # The main program that calls all the necessary routines for the rest.
    return

# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    logging.basicConfig(filename="HubDecoder.txt", filemode="w", level=LG_LVL,
                        format='%(asctime)s:%(levelname)s:%(message)s')


    try:
        main()
    
    except:
        # This won't work as it requires knowledge of the instances
        LoRa.exit_hub()
        Hub.exit_comms()
        print("Program Ended...")
        sys.exit()
