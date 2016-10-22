'''
Hub Data Decoder

'''
import logging
import time
import LoRaCommsReceiverV2
import LogFileWriter

# How long we wait for a data packet
COMMS_TIMEOUT = 2

# constants that will not change in program
# command bytes that are used by LoRa module
AssociationRequest = chr(0x30).encode('utf-8')
AssociationRequest = chr(0x31).encode('utf-8')
DataPacketFinal = chr(0x37).encode('utf-8')
Ping = chr(0x32).encode('utf-8')

# ack codes
ACK = chr(0x22).encode('utf-8')                 # all good and confirmed
NackPreamble = chr(0x50).encode('utf-8')        # preamble erro - ascii P
NackCRC = chr(0x51).encode('utf-8')             # CRC error - ascii Q
NackAddrError = chr(0x60).encode('utf-8')       # address error - ascii '
NackMsgLen = chr(0x61).encode('utf-8')          # message length inconsisten - ascii a
NackPayload = chr(0x70).encode('utf-8')         # payload crc error- ascii p
NackCmdRecog = chr(0x7A).encode('utf-8')        # command not recognised - ascii €
NackCmdSync = chr(0x7B).encode('utf-8')         # command out of protocol sync
NackNotReadyforData = chr(0x7C).encode('utf-8') # not ready for data ascii ,


# initialise global variables for data packet. Defined here so that they are global
Packet = b''  # start with empty packet.
# pointers in packet
StartHubAddr = 0  # poisiton in packet where hub addr starts
StartELBAddr = 5  # posiiton in packet where ELB starts
StartCommand = 10  # posiiton of command byte
StartPayloadLength = 11  # position of payload length byte
StartPayload = 12  # poition of start of payload
# TODO - check these pointers are true of ping, request to send and data packets
ExecByte = "!".encode('utf-8')      # The executive by

ZeroPayload = chr(0x00).encode('utf-8')           # used to indicate there is zero payload

# Initialise files

def DisplayMessage(Packet, message_type):
    # Takes the given packet of data splits it onto the screen / log file
    # message_type is the type of message
    src = Packet[StartHubAddr:StartHubAddr+4]
    dst = Packet[StartELBAddr:StartELBAddr+4]
    cmd = chr(Packet[StartCommand]).encode('utf-8')
    lgth = Packet[StartPayloadLength]
    payload = Packet[StartPayload:]
    print("Message %s" % message_type)
    logging.info("Message %s" % message_type)
    print("DST:%s SRC:%s CMD:%s LEN:%s PAY:%s\n" % (src, dst, cmd, lgth, payload))
    logging.info("DST:%s SRC:%s CMD:%s LEN:%s PAY:%s" % (src, dst, cmd, lgth, payload))

    return

def ValidatePayload (Packet):
    #
    # NOT USED - MOVED TO LogFileWriter
    #
    # checks payload of the packet and looks for CRC
    # assumes that only a packet with data is sent to this routine
    # checks if the first
    PayloadValid = False                                # assume payload is not valid
    PayloadLength = int(Packet[StartPayloadLength])     # get payload length
    Payload = Packet[StartPayload:StartPayload + PayloadLength]        # extract payload

    Checksum = 0                                  # zero checksum
    for i in range(PayloadLength):                  # check each byte in the payload
        Checksum = Checksum ^ int(Packet[StartPayload + i])

    logging.debug("[HDD] - Validating the payload is returning :%s" % Checksum ==0)
    return Checksum == 0        # checsum vald if equal to 0

def ValidatePacketOld (Packet):
    # routine to validate a packet that has been received
    # checks for 5th and 10th bytes to be '!' or '>'
    # checks length to ba ta least 12 bytes
    # for if command is DataPacketandReq or DataPacketFinal then it can perform a CRC on the payload

    ValidPacket = False         # assume packet is invalid
    if chr(Packet[StartHubAddr+4]).encode('utf-8') == b'!' or chr(Packet[StartHubAddr+4]).encode('utf-8') == b'>':
        # packet has valid 1st address descripters so continue
        if chr(Packet[StartELBAddr+4]).encode('utf-8') == b'!' or chr(Packet[StartELBAddr+4]).encode('utf-8') == b'>':
            # 2nd addr descripter valid so continue
            if len(Packet) >= 12:                       # packet is long enough so continue
                if chr(Packet[StartCommand]).encode('utf-8') == DataPacketandReq or \
                        chr(Packet[StartCommand]).encode('utf-8') == DataPacketFinal:
                            # now check payload
                   #ValidPacket = ValidatePayload(Packet) # Moved to log file writer
                   ValidPacket = True           # Validating of the payload moved to LogFileWriter
                elif chr(Packet[StartCommand]).encode('utf-8') == Ping or \
                            chr(Packet[StartCommand]).encode('utf-8') == DataToSendReq:
                    # no payload so only addr descripters and messag elength can be used
                    ValidPacket = True
    logging.info("[HDD] - Packet of data has been validated :%s" % Packet)
    return ValidPacket

def ValidatePacket (Packet):
    # routine to validate a packet that has been received
    # checks for 5th and 10th bytes to be '!' or '>'
    # checks length to ba ta least 12 bytes
    # for if command is DataPacketandReq or DataPacketFinal then it can perform a CRC on the payload

    ValidPacket = False         # assume packet is invalid
    if len(Packet) >= 12:                       # packet is long enough so continue
        if chr(Packet[StartHubAddr+4]).encode('utf-8') == b'!' or chr(Packet[StartHubAddr+4]).encode('utf-8') == b'>':
            # packet has valid 1st address descripters so continue
            if chr(Packet[StartELBAddr+4]).encode('utf-8') == b'!' or chr(Packet[StartELBAddr+4]).encode('utf-8') == b'>':
                # 2nd addr descripter valid so continue
                if chr(Packet[StartCommand]).encode('utf-8') == DataPacketandReq or \
                        chr(Packet[StartCommand]).encode('utf-8') == DataPacketFinal:
                            # now check payload
                   #ValidPacket = ValidatePayload(Packet) # Moved to log file writer
                   ValidPacket = True           # Validating of the payload moved to LogFileWriter
                elif chr(Packet[StartCommand]).encode('utf-8') == Ping or \
                            chr(Packet[StartCommand]).encode('utf-8') == DataToSendReq:
                    # no payload so only addr descripters and messag elength can be used
                    ValidPacket = True
    logging.info("[HDD] - Packet of data has been validated :%s" % Packet)
    return ValidPacket

def GetModuleData(sp, Simulate):
    # this module supplies a packet every time it is called
    # if simulating then packets are created and returned. The returned packet depends on the value of sp passed.

    if Simulate:
        # Simulation Packets
        HubAddr = b'0000!'
        Hub2Addr= b'2222!'
        ELB1Addr = b'1234!'
        ELB2Addr = b'5678!'
        ELB3Addr = b'9876!'


        ELB1_Ping = HubAddr +ELB1Addr + Ping + ZeroPayload  # zero payload on end
        ELB2_Ping = HubAddr +ELB2Addr + Ping + ZeroPayload
        ELB1_DataToSendReq = HubAddr + ELB1Addr + DataToSendReq + ZeroPayload
        ELB2_DataToSendReq = HubAddr + ELB2Addr + DataToSendReq + ZeroPayload
        HUB_to_ELB1_ClearToSendData = ELB1Addr + HubAddr + ClearToSendData + ZeroPayload
        HUB2_to_ELB3_ClearToSendData = ELB1Addr + HubAddr + ClearToSendData + ZeroPayload
        ELB1_DataPacketandReq = HubAddr + ELB1Addr + DataPacketandReq + \
                            chr(37).encode('utf-8')+ b'Data from ELB 1. More data to follow' + b'\x7d'
        ELB2_DataPacketandReq = HubAddr + ELB2Addr + DataPacketandReq + \
                            chr(37).encode('utf-8') + b'Data from ELB 2. More data to follow' + b'\x7e'
        ELB1_DataPacketFinal = HubAddr + ELB1Addr + DataPacketFinal + \
                            chr(30).encode('utf-8') + b'Data from ELB 1. Final Packet' + b'\x36'
        ELB2_DataPacketFinal = HubAddr + ELB2Addr + DataPacketFinal + \
                            chr(29).encode('utf-8') + b'Data from ELB 2. Final Packet' + b'\00'
        Hub_Ack_ELB1 = ELB1Addr + HubAddr + ACK + b'\x00'   # add zero payload on end
        Hub_Ack_ELB2 = ELB2Addr + HubAddr + ACK + b'\x00'
        ELB_Unrecognised = HubAddr + ELB1Addr + b'u' + ZeroPayload
        Hub_to_ELB1_Nack_NotReady = HubAddr + ELB1Addr + NackNotReadyforData + ZeroPayload
        Hub_to_ELB2_Nack_NotReady = HubAddr + ELB2Addr + NackNotReadyforData + ZeroPayload
        Hub_to_ELB1_Nack_Unrecog = HubAddr + ELB1Addr + NackCmdRecog + ZeroPayload
        Hub_to_ELB2_Nack_Unrecog = HubAddr + ELB2Addr + NackCmdRecog + ZeroPayload

        Payload = chr(0x7F) + chr(0x00) + chr(0x30) + \
                  chr(0x45) + chr(0x12) + chr(0x25) + chr(0x12) + chr(0x15) + chr(0x01) + chr(0x02) + chr(0x03) + \
                  chr(0x04) + chr(0x05) + chr(0x06) + chr(0x07) + chr(0x08) + chr(0x11) + chr(0x22) + chr(0x33) + \
                  chr(0x44) + chr(0x11) + chr(0x22) + chr(0x33) + chr(0x22) + chr(0x45) + chr(0x67) + chr(0x56) + \
                  chr(0x78) + chr(0x03) + chr(0xA4)
        Payload = Payload.encode('utf-8')
        '''
            ComsIdle = True
                Valid Commands =
                        Ping and SendDataReq
                Invalid Commnds =
                        ClearToSendData, DataPacketandReq, DataPacketFinal, Unrecognised
            ComsIdle = False
                Valid Commands =
                        DataPacketandReq and DataPacketFinal
                Invalid commands =
                        Ping, DataToSendReq, ClearToSendData, Unrecognised
                        DataPacketandReq from another ELB
                        DataPacketFinal from another ELB
        '''
        Simulation_Packets = [
                b'0000!\x00\x11$\xb4U2\x00',    # string from ELB
                ELB1_Ping,                      # 0: ELB1 ping
                ELB1_DataToSendReq,             # 1: ELB1 requesting to send data
                ELB1_DataPacketandReq,          # 2: Data from ELB. More to follow
                ELB1_DataPacketFinal,           # 3: final data from ELB1
                ELB1_Ping,                      # 3: ELB1 ping
                    # ComsIdle now True
                ELB1_DataPacketandReq,          # 5: Data from ELB with no ClearToSendData
                ELB1_DataPacketFinal,           # 6: Final data from ELB1 with no ClearToSend
                HUB2_to_ELB3_ClearToSendData,   # 7: Clear to send from another hub
                ELB_Unrecognised,               # 8: Unrecognised command
                ELB1_Ping,                      # 9: ELB1 ping
                ELB1_DataToSendReq,             # 10: ELB1 requesting to send data.
                    # ComsIdle now False
                ELB2_Ping,                      # 11: ping from ELB2 after data to send req
                ELB2_DataPacketandReq,          # 12: data packet from another ELB
                HUB2_to_ELB3_ClearToSendData,   # 13: Cler to Send from another hub
                ELB_Unrecognised,               # 14: Unrecognised command
                ELB1_DataPacketFinal,           # 15: Final data packet from ELB1
                    #ComsIdle now true
                ELB1_Ping,                      #16: ELB1 ping
                ELB2_Ping,                      # 17: ELB 2 ping
                ELB2_DataToSendReq,             # 18: Start coms with ELB 2
                ELB1_DataToSendReq,             # 19: ELB 1 tries to send data at teh same time
                ELB1_Ping,                      # 20: ELB 1 pings hub
                ELB2_DataPacketandReq,          # 21: ELB2 send data
                ELB1_DataToSendReq,             # 22: ELB1 tries again
                ELB1_DataPacketFinal,           # 23: ELB1 sends data
                ELB2_DataPacketFinal            # 24: final data from ELB2
            ]

        reply = Simulation_Packets[sp]

    else:
        # Running in normal mode
        # This function returns a packet of data as a string, only returns when data captured
        # Packet = []
        reply = LoRaCommsReceiver.ReturnRadioData(sp)

    logging.info(' ')  # force new lne
    logging.info("[HDD] - Comms Message received to process :%s" % reply)

    return reply

def WriteLogFile(Packet):
    # Takes the given log file and passes it to the writing routine

    ELBName = Packet[StartELBAddr:StartELBAddr+4]
        # Pass the ELB name into the logwriter
    PayloadLength = Packet[StartPayloadLength]     # get payload length as int
    DataToWrite = Packet[StartPayload:StartPayload+PayloadLength]
    logging.debug("[HDD] - Data to write from ELB:%s, this length %s this data:%s" % (ELBName, PayloadLength, DataToWrite))

    if Simulate != True:
        LogFileWriter.LogFileCreation(ELBName, DataToWrite)

    else:
        print("\n[HDD] - Data to be written:\n %s \n" % DataToWrite)
    return

def GenerateAck(Packet):
    # Function generates an Ack for response to a number of messages
    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr+4]   # Receiver address
    packet_to_send = packet_to_send + ExecByte                                         # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr+4]    # Sender address
    packet_to_send = packet_to_send + ExecByte                     # Executive Byte
    packet_to_send = packet_to_send + ACK                     # Acknowledge
    packet_to_send = packet_to_send + ZeroPayload                   # add zero payload length

    return packet_to_send


def RespondToPing(fd, Packet,Simulate):

    message = GenerateAck(Packet)
    DisplayMessage(message, "SEND: Ping Acknowledge")
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)
    return

def RespondDataPacketandReq(fd, Packet, Simulate):
    # data packet received and further data is on its way

    message = GenerateAck(Packet)
    DisplayMessage(message, "SEND: Data Packet + Req Acknowledge")
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)


def RespondDataPacketFinal(fd, Packet, Simulate):
    # data packet received and no more to come

    message = GenerateAck(Packet)
    DisplayMessage(message, "SEND: Data Packet Final Acknowledge")
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)

def RespondDataToSendReq(fd, Packet,Simulate):
    # responds to the Data to Send Request

    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr+4]   # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byt
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr+4]   # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + ClearToSendData                       # Clear to Send data command
    packet_to_send = packet_to_send + ZeroPayload                               # add zero payload length

    DisplayMessage(packet_to_send, "SEND: Clear to Send Data")
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)

def UnrecognisedCommand(fd,Packet,Simulate):
    # send relevant Nack.

    # Function generates an Ack for response to anumber of messages
    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr + 4] # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr + 4] # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + NackCmdRecog                          # Nack with command unrecognised
    packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

    DisplayMessage(packet_to_send, "SEND: NACK CMD Not Recognised")
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)


def SendPiBusyNack(fd,Packet,Simulate):
    # have been pinged from 2nd ELB while receiving data from 1st ELB
    # Function generates an Ack for response to anumber of messages
    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr + 4] # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr + 4] # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + NackNotReadyforData                   # Nack with command unrecognised
    packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

    DisplayMessage(packet_to_send, "SEND: NACK Not Ready For Data")
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)

def RespondErrorInPayload(fd,Packet,Simulate):
    # The payload received is not valid, so reject it
    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr + 4] # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr + 4] # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + NackPayload                           # Nack with Error In Payload
    packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length

    DisplayMessage(packet_to_send, "SEND: NACK Error In Payload")
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)

def Main():
    # initialise variables
    ComsIdle = True  # set to false when an initial RequestToSendData has been received.
    CurrentELB = b''  # when coms has started this variable holds the ELB addr that we are talking to
    TimeLastValidPacket = time.time()       # reset time of last valid packet
    PreviousPacket = b'empty'       # Set to a default value that is never expected to be received.

    if Simulate != True:
        # Open the serial port and configure the Radio Module
        LoRaCommsReceiver.SetupGPIO()
        SerialPort = LoRaCommsReceiver.SetupUART()
        LoRaCommsReceiver.SetupLoRa(SerialPort)
    else:
        SerialPort = 0

    while True:
        i=0
        #print("NEW LOOP IN MAIN", flush=True)
    #for i in range(25):
        '''
        The struture of the main loop is to loop forever getting data and then processing it.
        3 variables indicate if
            coms is idle - no conversation has been started
            a packet has been received - data received, validated and acked. Ready to write
            who we are talking to - the ELB address that has started a conversation
        '''
        if Simulate:
            Packet = GetModuleData(i, Simulate)
        else:
            Packet = GetModuleData(SerialPort,Simulate)
            # waits in Get data until we have now received a packet from the radio module and it has been checked for validity

        if ValidatePacket(Packet):       # is this a valid packet
            TimePacketReceived = time.time()        # The time the last valid packet was received
            Command = chr(Packet[StartCommand]).encode('utf-8')          # extract command byte as byte String

            if (TimePacketReceived - TimeLastValidPacket) > COMMS_TIMEOUT:
                # this data packet was received outside the comms window
                DisplayMessage(Packet, "RECV: Packet received outside COMMS_TIMEOUT window")
                ComsIdle = True

            if ComsIdle:  # not yet in communication with an ELB
                if Command == Ping:
                    DisplayMessage(Packet, "RECV: Ping")
                    RespondToPing(SerialPort,Packet,Simulate) # respond to a ping command
                elif Command == DataToSendReq:
                    ComsIdle = False                            # coms has started so no longer idle
                    DisplayMessage(Packet, "RECV: Data To Send Request")
                    CurrentELB = Packet[StartELBAddr:StartELBAddr+4]
                    if USE_TIME:
                        # The Settings.py program has this value set, so only send comms within a timed window
                        # Find the current time, setting the date to a default rather than current so it is ignored
                        just_now = datetime.datetime.now().replace(year=1900, month=1, day=1)
                        if just_now > START_COMMS_TIME and just_now < STOP_COMMS_TIME:
                            RespondDataToSendReq(SerialPort,Packet,Simulate)
                            TimeLastValidPacket = TimePacketReceived
                        else:
                            # We need to respond with a negative and send a Pi Busy NACK
                            ComsIdle = True
                            DisplayMessage(Packet,"RECV: Message Outside Comms Window")
                            SendPiBusyNack(SerialPort,Packet,Simulate)
                    else:
                        RespondDataToSendReq(SerialPort,Packet,Simulate)
                        TimeLastValidPacket = TimePacketReceived # time.time()
                    # this will send CleartoSendData.
                elif Command == ClearToSendData or Command == DataPacketandReq or Command == DataPacketFinal:
                    # commands invalid at this point
                    DisplayMessage(Packet, "RECV: Message Sequence incorrect")
                    logging.info("[HDD] - ClearToSendData, DataPacketandReq or DataPacketFinal at wrong time :%s" % Packet)
                else:
                    DisplayMessage(Packet, "RECV: Unrecognised Command")
                    UnrecognisedCommand(SerialPort, Packet, Simulate)
                        # send Nack with unrecognised cmd
            else:                                   # ComsIdle is true so talking to ELB
                if Command == DataPacketandReq and CurrentELB == Packet[StartELBAddr:StartELBAddr+4]:
                        # coms has started and received data packet with more to follow
                    if (Packet == PreviousPacket): #and (Packet[StartPayload+1:StartPayload+7] != b'\xff\xff\xff\xff\xff\xff'):
                        # Check for duplicated packet but not full of FF's
                        # The ff's was added to deal with data recevied from the EWC being resent as the hub rejecting it
                        # as duplicate. data contaiing ff's is now passed through and ignored by the data file writer.
                        DisplayMessage(Packet, "RECV: Duplicate Packet Seen")
                        RespondDataPacketandReq(SerialPort,Packet,Simulate)     # send ack packet
                        TimeLastValidPacket = TimePacketReceived # time.time()
                    else:
                        PreviousPacket = Packet
                        DisplayMessage(Packet, "RECV: Data Packet and Request")
                        # take out
                        RespondDataPacketandReq(SerialPort,Packet,Simulate)     # send ack packet
                        TimeLastValidPacket = TimePacketReceived # time.time()
                        WriteLogFile(Packet)            # write this packet to a log file
                elif Command == DataPacketFinal and CurrentELB == Packet[StartELBAddr:StartELBAddr+4]:
                    # Comms has started and received final data packet
                    DisplayMessage(Packet, "RECV: Data Packet Final")
                    RespondDataPacketFinal(SerialPort,Packet,Simulate)
                    if Packet == PreviousPacket:        # Check for duplicated packet
                        DisplayMessage(Packet, "RECV: Duplicate Packet Seen")
                    else:
                        PreviousPacket = Packet
                    WriteLogFile(Packet)                            # write this packet to a log file
                    ComsIdle = True                                 # coms sequence comlete so reset coms idle
                    CurrentELB = ''                                 # clear current ELB
                elif Command == DataPacketandReq and CurrentELB != Packet[StartELBAddr:StartELBAddr+4]:
                    # coms has started and received data packet from wrong ELB
                    DisplayMessage(Packet, "RECV: Data Packet request when Pi Busy with another ELB")
                    SendPiBusyNack(SerialPort, Packet, Simulate)  # send Pi busy Nack
                elif Command == DataPacketFinal and CurrentELB != Packet[StartELBAddr:StartELBAddr+4]:
                    # coms has started and received data packet from wrong ELB
                    DisplayMessage(Packet, "RECV: Data Packet Final when Pi Busy with another ELB")
                    SendPiBusyNack(SerialPort, Packet, Simulate)  # send Pi busy Nack

                else:                               # handle invalid command
                    if Command == Ping:                               # received ping from another ELB while receiving data
                        DisplayMessage(Packet, "RECV: Ping")
                        RespondToPing(SerialPort,Packet,Simulate)      # send Ack to ping
                    elif Command == DataToSendReq or Command == ClearToSendData:
                        logging.info("[HDD] - DataToSendReq or ClearToSendData when already in coms :%s" % Packet)
                    else:
                        DisplayMessage(Packet, "RECV: Unrecognised Command")
                        UnrecognisedCommand(SerialPort, Packet, Simulate)
                        # send Nack with unrecognised cmd
        else:
            logging.info("[HDD] - This data is invalid :%s" % Packet)
            print("[HDD] - This data is invalid :%s" % Packet)      # send message to execution window


# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    logging.basicConfig(filename="HubDecoder.txt", filemode="w", level=LG_LVL,
                        format='%(asctime)s:%(levelname)s:%(message)s')



    Main()
