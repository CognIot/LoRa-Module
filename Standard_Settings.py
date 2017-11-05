# Customer file locations
OPFILE_NAME = "custfile.txt"
OPFILE_LOCATION = "."

#Recordfile locations
RECORDFILE_LOCATION = "DataFiles"           # Where to store the records file, program automatically added '/' at the end
RECORDFILE_NAME = "DATA_"            # The Base name part of the file
RECORDFILE_EXT = ".rec"             # The extension for the record files
RECORDFILE_OLD = ".oldrec"          # The extension used when the record can't be written and is stored for future analysis
RECORD_TRY_COUNT = 10               # How many times, when connected the Data Accessor will try and send a record
EEPROM_READ_RETRY = 5               # How many times it will try and read data from the EEPROM

#Comms general values
REPLY_WAIT = 5                      # How long to wait for a response
RETRIES = 5                         # How many attempts to take to communicate


def test():

    return

