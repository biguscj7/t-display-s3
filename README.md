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

### Installing

* Use esptool.py to install firmware to board

```
esptool.py --chip esp32s3 --port /dev/<PORT> erase_flash
```
```
esptool.py --chip esp32s3 --port /dev/<PORT> write_flash -z 0x1000 firmware.bin
```

### Executing program

Configure data.txt with wifi credentials for desired networks

Coordinate registration of device with Adam Smith to associate specific display with specific QW Workspace
* Devices are registered by associated their MAC address with a specific unit on the QW reservation app server.
* On boot the device should show its mac address if it fails the registration flow

## Help

Contact Sheffield Tech Ops at [tech-ops@thebrieflab.com](mailto:tech-ops@thebrieflab.com)

## Authors

Contributors names and contact info

Mark Nyberg  
[mnyberg@thebrieflab.com](mailto:mnyberg@thebrieflab.com)
