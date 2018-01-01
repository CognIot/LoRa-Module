#! /bin/sh

# Shell script to run pineapple Pi Application on bootup

cd /home/pi/Projects/LoRa-Module

sudo ./DataTransfer.py --node &

exit 0

