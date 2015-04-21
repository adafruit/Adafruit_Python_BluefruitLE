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

from Adafruit_BluetoothLE.bluezle_dbus import bluez
from Adafruit_BluetoothLE.services import UART, DeviceInformation


# Initialize communication with bluez.  MUST be called before any other bluez
# calls are made.
bluez.initialize()

# Useful debugging information to print the tree of bluez DBus objects.
#bluez._print_tree()

# Make sure any connected device is disconnected and the adapter stops scanning
# before exiting.
def cleanup():
    # Disconnect any connected device.
    for device in bluez.list_devices():
        if device.connected:
            device.disconnect()
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

# Remove any devices that are known before scanning.
for device in bluez.list_devices():
    device.remove()

# Start scan for devices.
print 'Scanning...'
adapter.start_scan()

# Spend up to 30 seconds waiting for a UART device to be found.
device = UART.find_device(timeout_sec=30)
if device is not None:
    print 'Found device {0}!'.format(device.name)
else:
    print 'Failed to find UART device!'
    sys.exit(-1)

adapter.stop_scan()

time.sleep(1)

# Connect to device.
print 'Connecting...'
device.connect()

# Wait for services to discover.
print 'Waiting for service discovery...'
if not UART.discover_services(device, timeout_sec=60):
    print 'Failed to discover UART service data!'
    sys.exit(-1)
#if not DeviceInformation.discover_services(device, timeout_sec=60):
#    print 'Failed to discover device information service data!'
#    sys.exit(-1)

#device._device.ConnectProfile('0000180A-0000-1000-8000-00805F9B34FB')

## Get the device information service and print out some device info.
#dis = DeviceInformation(device)
#print 'Manufacturer:', dis.manufacturer
#print 'Model:', dis.model
#print 'HW Revision:', dis.hw_revision
#print 'SW Revision:', dis.sw_revision
#print 'FW Revision:', dis.fw_revision

# Create a UART service from the device.
print 'Creating UART device and sending message...'
uart = UART(device)

# Send a message to the UART.
uart.write('Hello world!\r\n')

# Loop reciving data from the UART:
print 'Waiting for messages from device...'
while True:
    # Block indefinitely waiting for data to be received.
    #data = uart.read()
    # Can optionally call read with a timeout in seconds.  If the timeout is
    # exceeded before receiving data then None is returned.
    data = uart.read(3)  # Wait 3 seconds for data
    if data is None:
       print 'Exceeded timeout waiting for data!'
       continue
    print 'Received:', data
