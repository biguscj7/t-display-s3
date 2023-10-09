#!/bin/bash
#

export AMPY_PORT=/dev/tty.usbmodem1234561

for OUTPUT in $(ampy ls)
do
   ampy rm $OUTPUT
done

for INPUT in display_helpers.py romans.py tft_config.py
do
    ampy put ../$INPUT
done

ampy put ../demo-working.py main.py
