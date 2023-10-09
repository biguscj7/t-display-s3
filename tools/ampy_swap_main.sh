#!/bin/bash
#

export AMPY_PORT=/dev/tty.usbmodem1234561

ampy rm main.py
ampy rm wifimgr.py

ampy put ../main-working.py main.py
ampy put ../wifimgr.py wifimgr.py
