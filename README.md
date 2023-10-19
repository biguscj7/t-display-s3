# t-display-S3 / QW Timer

IoT device for indicating end of reservation window.

## Description

This project is to produce an IoT connected device that displays messages and indications related to the reservation
status of an individual QW Workspace.

## Getting Started

### Dependencies

* Micropython firmware from: [Russ Hughes t-display-s3 port](https://github.com/russhughes/st7789s3_mpy.git)
* [Lilygo T-Display-S3 hardware](https://www.lilygo.cc/products/t-display-s3?variant=42284559827125) 
  * Not soldered / non-touch version

* Future use: https://github.com/russhughes/s3lcd
  * This is a micropython driver for the LCD display on the T-Display-S3 board, but it is not yet complete.

* Configuration / firmware loading
  * ampy
  * esptool

### Installing

* Use esptool.py to install firmware to board

```
esptool.py --chip esp32s3 --port /dev/<PORT> erase_flash
```
```
esptool.py --chip esp32s3 --port /dev/<PORT> write_flash -z 0 firmware.bin
```

### Executing program

Configure data.txt with wifi credentials for desired networks

Scripts in the 'tools' folder allow easy movement of required files onto the
units. They are bash scripts and presume a UNIX environment where the device 
registers as "/dev/tty.usbmodem1234561".

Example:
```
bash ampy_swap.sh
```
This will copy all the required files to the device. Ensure wifi credentials have been 
appropriately configured in data.txt.

Coordinate registration of device with Adam Smith to associate specific display with specific QW Workspace
* Devices are registered by associated their MAC address with a specific unit on the QW reservation app server.
* On boot the device should show its mac address if it fails the registration flow

## Help

Contact Sheffield Tech Ops at [tech-ops@thebrieflab.com](mailto:tech-ops@thebrieflab.com)

## Authors

Contributors names and contact info

Mark Nyberg  
[mnyberg@thebrieflab.com](mailto:mnyberg@thebrieflab.com)
