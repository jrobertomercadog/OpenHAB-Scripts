These files are code for accessing a BLE beacon and passing the values via MQTT transport for use in OpenHAB.

Currently the scan file is specific for a Blue Maestro Tempo Disc.

jrobertomercadog Notes:
Tested on a Raspberry Pi Zero W "Raspbian Buster" with:
* kernel 5.4.35+ #1314 Fri May 1 17:36:08 BST 2020 armv6l GNU/Linux (use: sudo rpi-update)
* Python 3.7.3
* bluez 5.50-1.2~deb10u1+rpt1
* pybluez 0.23

Steps followed:
* Download a fresh "Raspbian Buster Lite" image from https://www.raspberrypi.org/downloads/raspbian/
* Format your uSD using SD Card Formatter: https://www.sdcard.org/downloads/formatter/
* Write the IMG to your uSD. I use balenaEtcher: https://www.balena.io/etcher/
* Create a "ssh" file: https://www.raspberrypi.org/documentation/remote-access/ssh/README.md
* Create a wpa_supplicant file: https://www.raspberrypi.org/documentation/configuration/wireless/headless.md
* Install the uSD into your Raspberry Pi Zero W
* Login with user pi
* Execute: sudo apt-get update
* Execute: sudo apt-get upgrade
* Execute: sudo apt-get clean
* Execute: sudo rpi-update
* Reboot
* Login again with user pi
* Execute: sudo apt-get install python3-pip
* Execute: sudo -H pip3 install --upgrade pip
* Execute: sudo -H pip3 install pybluez
* Run the test: sudo python3 bluemaestroscan.py
* Have fun!
