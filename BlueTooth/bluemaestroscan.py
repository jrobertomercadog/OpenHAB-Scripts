#BlueMastro Tempo Disc Advertising packet decoder# Called from bluemaestro.py# This class has the specificis
#for decoding the advertising packets for the Blue Maestro Tempo Disc https: //www.bluemaestro.com/product/tempo-disc-temperature/
#Unsure if there are any other Blue Maestro products that #would work with.
#David@andc.nz 15 / 12 / 2016

#BLE Scanner based on from JCS 06 / 07 / 14
#BLE scanner based on https: //github.com/adamf/BLE/blob/master/ble-scanner.py
#BLE scanner, based on https: //code.google.com/p/pybluez/source/browse/trunk/examples/advanced/inquiry-with-rssi.py
#https://github.com/pauloborges/bluez/blob/master/tools/hcitool.c for lescan
#https://kernel.googlesource.com/pub/scm/bluetooth/bluez/+/5.6/lib/hci.h for opcodes
#https://github.com/pauloborges/bluez/blob/master/lib/hci.c
#L2782 for functions used by lescan
#performs a simple device inquiry, and returns a list of ble advertizements discovered device
#NOTE: Python 's struct.pack() will add padding bytes unless you make the endianness explicit. Little endian should be used for BLE.Always start a struct.pack() format string with "<"

#Forked from psyciknz/OpenHAB-Scripts
#Tested on a Raspberry Pi Zero W Raspbian Buster with:
#kernel 5.4.35+ #1314 Fri May 1 17:36:08 BST 2020 armv6l GNU/Linux
#Python 3.7.3
#bluez 5.50-1+rpt1
#pybluez 0.23
#..And few python3 syntax modifications by jrobertomercadog.
#THIS CODE IS A WORK-IN-PROGRESS: I haven't properly parsed battery level/voltage, and the UUID (udid?) still looks funny.

DEBUG = False

import collections
import os
import sys
import struct
import bluetooth._bluetooth as bluez

LE_META_EVENT = 0x3e
LE_PUBLIC_ADDRESS = 0x00
LE_RANDOM_ADDRESS = 0x01
LE_SET_SCAN_PARAMETERS_CP_SIZE = 7
OGF_LE_CTL = 0x08
OCF_LE_SET_SCAN_PARAMETERS = 0x000B
OCF_LE_SET_SCAN_ENABLE = 0x000C
OCF_LE_CREATE_CONN = 0x000D

LE_ROLE_MASTER = 0x00
LE_ROLE_SLAVE = 0x01

# these are actually subevents of LE_META_EVENT
EVT_LE_CONN_COMPLETE = 0x01
EVT_LE_ADVERTISING_REPORT = 0x02
EVT_LE_CONN_UPDATE_COMPLETE = 0x03
EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE = 0x04

# Advertisment event types
ADV_IND = 0x00
ADV_DIRECT_IND = 0x01
ADV_SCAN_IND = 0x02
ADV_NONCONN_IND = 0x03
ADV_SCAN_RSP = 0x04

def returnnumberpacket(pkt):
  myInteger = 0
  multiple = 256
  for c in pkt:
    myInteger += struct.unpack("B", c.to_bytes(1, 'big'))[0] * multiple
    multiple = 1
  return myInteger

def returnstringpacket(pkt):
  myString = "";
  for c in pkt:
    myString += "%02x" % struct.unpack("B", c.to_bytes(1, 'big'))[0]
  return myString

def returnfulldecode(pkt):
  myString = "";
  bdata = list()
  for c in pkt:
    bdata.append(struct.unpack("B", c.to_bytes(1, 'big'))[0])
  myString = "".join(map(chr, bdata))
  return myString

def printpacket(pkt):
  for c in pkt:
    sys.stdout.write("%02x " % struct.unpack("B", c.to_bytes(1, 'big'))[0])

def get_packed_bdaddr(bdaddr_string):
  packable_addr = []
  addr = bdaddr_string.split(':')
  addr.reverse()
  for b in addr:
    packable_addr.append(int(b, 16))
  return struct.pack("<BBBBBB", * packable_addr)

def packed_bdaddr_to_string(bdaddr_packed):
  return ':'.join('%02x' % i for i in struct.unpack("<BBBBBB", bdaddr_packed[::-1]))

def hci_enable_le_scan(sock):
  hci_toggle_le_scan(sock, 0x01)

def hci_disable_le_scan(sock):
  hci_toggle_le_scan(sock, 0x00)

def hci_toggle_le_scan(sock, enable):
  cmd_pkt = struct.pack("<BB", enable, 0x00)
  bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)

def hci_le_set_scan_parameters(sock):
  old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)

SCAN_RANDOM = 0x01
OWN_TYPE = SCAN_RANDOM
SCAN_TYPE = 0x01

def parse_events(sock, loop_count = 100):
  old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)
# perform a device inquiry on bluetooth device #0
# The inquiry should last 8 * 1.28 = 10.24 seconds# before the inquiry is performed, bluez should flush its cache of previously discovered devices
  flt = bluez.hci_filter_new()
  bluez.hci_filter_all_events(flt)
  bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
  sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)
  done = False
  results = []
  myFullList = {}
  for i in range(0, loop_count):
    pkt = sock.recv(255)
  ptype, event, plen = struct.unpack("BBB", pkt[: 3])
  if event == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
    i = 0
  elif event == bluez.EVT_NUM_COMP_PKTS:
    i = 0
  elif event == bluez.EVT_DISCONN_COMPLETE:
    i = 0
  elif event == LE_META_EVENT:
    subevent, = struct.unpack("B", pkt[3].to_bytes(1, 'big'))
    pkt = pkt[4: ]
    if subevent == EVT_LE_CONN_COMPLETE:
      le_handle_connection_complete(pkt)
    elif subevent == EVT_LE_ADVERTISING_REPORT:
      num_reports = struct.unpack("B", pkt[0].to_bytes(1, 'big'))[0]
      report_pkt_offset = 0
      for i in range(0, num_reports):
        company = returnstringpacket(pkt[report_pkt_offset + 15: report_pkt_offset + 17])
        if (DEBUG == True):
          print ("===============================================================================================================")
        if (DEBUG == True):
          print ("\tfullpacket: ")
          printpacket(pkt)
        if (company == "3301"):
          if (DEBUG == True):
            print ("\tCompany: ", company)
          udid = returnstringpacket(pkt[report_pkt_offset + 22: report_pkt_offset - 6])
          if (DEBUG == True):
            print ("\tUDID: ", udid)
          myFullList["udid"] = udid
          if (DEBUG == True):
            print ("\tMAJOR: ", printpacket(pkt[report_pkt_offset - 6: report_pkt_offset - 4]))
            print ("\tMINOR: ", printpacket(pkt[report_pkt_offset - 4: report_pkt_offset - 2]))
          mac = packed_bdaddr_to_string(pkt[report_pkt_offset + 3: report_pkt_offset + 9])
          myFullList["mac"] = mac
          if (DEBUG == True):
            print ("\tMAC Address string: ", mac)
          temp = float(returnnumberpacket(pkt[report_pkt_offset + 23: report_pkt_offset + 25])) / 10
          if (DEBUG == True):
            print ("\tTemp: ", temp)
          myFullList["temp"] = temp
          if (DEBUG == True):
            print ("\tHumidity: ", printpacket(pkt[report_pkt_offset + 25: report_pkt_offset + 27]))
          humidity = float(returnnumberpacket(pkt[report_pkt_offset + 25: report_pkt_offset + 27])) / 10
          if (DEBUG == True):
            print ("\tHumidity: ", humidity)
          myFullList["humidity"] = humidity
          dewpoint = float(returnnumberpacket(pkt[report_pkt_offset + 27: report_pkt_offset + 29])) / 10
          if (DEBUG == True):
            print ("\tDewpoint: ", dewpoint)
          myFullList["dewpoint"] = dewpoint
          nameLength = int(pkt[report_pkt_offset + 32])
          if (DEBUG == True):
            print ("\tNameLength: ", nameLength)
          name = returnfulldecode(pkt[report_pkt_offset + 33: report_pkt_offset + (33 + nameLength)])
          if (DEBUG == True):
            print ("\tName: %s %d " % (name, nameLength))
          myFullList["name"] = name
          battery = float(float((pkt[report_pkt_offset + 18]) / float(25500)) * 100)
          if (DEBUG == True):
            print ("\tBattery: ", battery)
          myFullList["battery"] = battery
          done = True
        else :
          if (DEBUG == True):
            print ("\tNon blue maestro packet found")
  sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, old_filter)
  return myFullList

#test code
dev_id = 0
sock = bluez.hci_open_dev(dev_id)
hci_le_set_scan_parameters(sock)
hci_enable_le_scan(sock)
thisdict = parse_events(sock, 2)
for x, y in thisdict.items():
  print(x, y)
