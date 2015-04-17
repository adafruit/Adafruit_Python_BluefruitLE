# Raw bluezle UART service communication example.  
# !! This will be greatly simplified with an explicit UART service class !!
# 
# Dependencies:
#
# - Must have bluez 5.3 installed.  Older version don't have complete BLE support
#   in their DBus API.
#
#   - For ubuntu use this PPA: https://launchpad.net/~vidplace7/+archive/ubuntu/bluez5
#       sudo apt-add-repository ppa:vidplace7/bluez5
#       sudo apt-get update
#       sudo apt-get install --upgrade bluez
#     Next things get a little hacky since bluetoothd needs to be run with the --experimental
#     flag.  Edit 
#
#   - For raspbian install from source (following similar instructions as the Pi
#     beacon guide: https://learn.adafruit.com/pibeacon-ibeacon-with-a-raspberry-pi/setting-up-the-pi)
#       sudo apt-get update
#       sudo apt-get install -y build-essential libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev
#       cd ~
#       wget http://www.kernel.org/pub/linux/bluetooth/bluez-5.30.tar.gz
#       tar xvfz bluez-5.30.tar.gz
#       cd bluez-5.30
#       ./configure --disable-systemd
#       make
#       sudo make install
#       sudo cp ./src/bluetoothd /usr/local/bin/
#     Now you need to add a line to /etc/rc.local to make bluetoothd run at start.
#     Run sudo nano /etc/rc.local and add this line before the exit 0:
#       /usr/local/bin/bluetoothd --experimental &
#     Reboot and bluetoothd should be running.
#
import atexit
import sys
import time
import uuid

from bluezle_dbus import bluez
from bluezle_dbus.services import UART


# Define service and characteristic UUIDs.
UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')

# Global variable to hold UART device that is later found.  Needed as global to
# cleanup later.
found = None


# Initialize communication with bluez.  MUST be called before any other bluez
# calls are made.
bluez.initialize()

# Useful debugging information to print the tree of bluez DBus objects.
#bluez._print_tree()

# Make sure any connected device is disconnected and the adapter stops scanning
# before exiting.
def cleanup():
    if found is not None:
        found.disconnect()
    # Stop any bluetooth adapters that are scanning.
    for adapter in bluez.list_adapters():
        if adapter.discovering:
            adapter.stop_scan()
atexit.register(cleanup)

# Pick the first bluetooth adapter found.
adapter = bluez.get_default_adapter()
print 'Using adapter {0}...'.format(adapter.name)

# Check that adapter is powerd on.
if not adapter.powered:
    print 'Powering on adapter...'
    adapter.powered = True

# Check if UART devices are already paired and unpair all of them.
for device in bluez.find_devices(UART_SERVICE_UUID):
    if device.paired:
        print 'Unpairing device {0}...'.format(device.name)
        device.unpair()

# Start scan for devices.
print 'Scanning...'
adapter.start_scan()

# Spend up to 30 seconds searching for a UART device.
i = 0
while True:
    # Look for a device that advertises the UART service and break out of the
    # loop when found.
    found = bluez.find_device(UART_SERVICE_UUID)
    if found is not None:
        print 'Found device {0}...'.format(found.name)
        break
    # Continue up to 30 seconds waiting for a device and then time out.
    i += 1
    if i >= 30:
        raise RuntimeError('Timeout waiting for UART device!')
    time.sleep(1)

# Pair with device and connect to receive all the GATT services.
if not found.paired:
    print 'Pairing...'
    found.pair()
found.connect()

# Create a UART service from the device.
uart = UART(found)

# Send a message to the UART.
uart.write('Hello world!\r\n')

# Loop reciving data from the UART:
print 'Waiting for messages from device...'
while True:
    data = uart.read()
    print 'Received:', data
