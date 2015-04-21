import atexit
import sys
import time

import dbus
from Adafruit_BluetoothLE.bluezle_dbus import bluez
from Adafruit_BluetoothLE.services import Colorific


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
device = Colorific.find_device(timeout_sec=30)
if device is not None:
    print 'Found device {0}!'.format(device.name)
else:
    print 'Failed to find colorific device!'
    sys.exit(-1)

adapter.stop_scan()

time.sleep(1)

# Connect to device.
print 'Connecting...'
device.connect()

# Wait for services to discover.
print 'Waiting for service discovery...'
if not Colorific.discover_services(device, timeout_sec=60):
    print 'Failed to discover colorific service data!'
    sys.exit(-1)

colorific = Colorific(device)
colorific.set_color(255, 0, 0)
print 'Done!'