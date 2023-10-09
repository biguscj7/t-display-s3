#!/bin/bash
#

export AMPY_PORT=/dev/tty.usbmodem1234561

for OUTPUT in $(ampy ls)
do
   ampy rm $OUTPUT
done

for INPUT in data.txt display_helpers.py mytime.py romans.py server_tools.py tft_config.py wifimgr.py
do
    ampy put ../$INPUT
done

ampy put ../main-working.py main.py
