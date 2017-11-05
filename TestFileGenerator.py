#!/usr/bin/env python3
"""
Test File Generator


"""
from datetime import datetime
from datetime import timedelta
import time
import Standard_Settings as SS
import json
import random

def write_data_to_file(data_to_write):
    """
    Takes the given data and creates a new file with the contents of it
    Format of the filename is based on standard settings
        RECORDFILE_NAME+tiemstamp+RECORDFILE_EXT
    Stored in sub folder
        RECORDFILE_LOCATION
    Returns true if the record is written, or false if it isn't
    Disk space management is handled by the calling program
    """
    status = False
    file_time = datetime.now().strftime("%y%m%d%H%M%S-%f")

    data_record_name = SS.RECORDFILE_LOCATION + '/' + SS.RECORDFILE_NAME + file_time + SS.RECORDFILE_EXT

    #TODO: Need to handle a failure to open the file
    with open(data_record_name, mode='w') as f:
        json.dump(data_to_write, f)
        status = True
    return status

def generate_timestamp():
    """
    Generate a timestamp of the correct format
    """
    now = str(datetime.now())
    return str(now[:23])
    
def generate_data():
    """
    Generate the data required and return it
    [[type, value, units, timestamp],[type, value, units, timestamp]]

    """
    sensor_type = 1
    value = random.randint(0,100)
    units = 'Lux'
    timestamp = generate_timestamp()

    return [[sensor_type, value, units, timestamp]]

def main():
    """
    Generate data and write it
    """
    while True:
        #Repeatably write a file
        status = False
        file_time = datetime.now().strftime("%y%m%d%H%M%S-%f")

        #TODO: If the datafile directoryu doesn't exist, an error is thrown!

        data_record_name = SS.RECORDFILE_LOCATION + '/' + SS.RECORDFILE_NAME + file_time + SS.RECORDFILE_EXT

        #TODO: Need to handle a failure to open the file
        with open(data_record_name, mode='w') as f:
            json.dump(generate_data(), f)
            status = True
        time.sleep(random.randint(0,100) /10)
        
    
    return

if __name__ == "__main__":

    main()
