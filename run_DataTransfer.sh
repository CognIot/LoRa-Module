#! /bin/sh

# Shell script to run LoRa Data Transer application on bootup

#As a NODE

cd /home/pi/Projects/LoRa-Module

sudo ./DataTransfer.py --node &

exit 0

