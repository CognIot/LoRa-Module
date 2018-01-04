#! /bin/sh

# Shell script to run LoRa Data Transer application on bootup

#As a HUB

cd /home/pi/Projects/LoRa-Module

sudo ./DataTransfer.py --hub &

exit 0

