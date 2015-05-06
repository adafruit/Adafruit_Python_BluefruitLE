# Base class for a BLE network adapter.  Each OS supported by the library should
# inherit from this class and implement the abstract methods.
# Author: Tony DiCola
import time

import objc

from ..interfaces import Adapter
from ..platform import get_provider


# Load IOBluetooth functions for controlling bluetooth power state.
objc.loadBundleFunctions(
    objc.loadBundle("IOBluetooth", globals(), bundle_path=objc.pathForFramework(u'/System/Library/Frameworks/IOBluetooth.framework')), 
    globals(), 
    [('IOBluetoothPreferenceGetControllerPowerState', 'oI'),('IOBluetoothPreferenceSetControllerPowerState','vI')]
)


class CoreBluetoothAdapter(Adapter):
    """CoreBluetooth BLE network adapter.  Note that CoreBluetooth has no
    concept of individual BLE adapters so any instance of this class will just
    interact with BLE globally.
    """

    def __init__(self):
        """Create an instance of the bluetooth adapter from the provided bluez
        DBus object.
        """
        self._is_scanning = False

    @property
    def name(self):
        """Return the name of this BLE network adapter."""
        # Mac OSX has no oncept of BLE adapters so just return a fixed value.
        return "Default Adapter"

    def start_scan(self, timeout_sec):
        """Start scanning for BLE devices."""
        get_provider()._central_manager.scanForPeripheralsWithServices_options_(None, None)
        self._is_scanning = True

    def stop_scan(self, timeout_sec):
        """Stop scanning for BLE devices."""
        get_provider()._central_manager.stopScan()
        self._is_scanning = False

    @property
    def is_scanning(self):
        """Return True if the BLE adapter is scanning for devices, otherwise
        return False.
        """
        return self._is_scanning

    def power_on(self):
        """Power on Bluetooth."""
        # Turn off bluetooth.
        IOBluetoothPreferenceSetControllerPowerState(0)
        time.sleep(2)

    def power_off(self):
        """Power off Bluetooth."""
        # Turn on bluetooth.
        IOBluetoothPreferenceSetControllerPowerState(1)
        time.sleep(2)

    @property
    def is_powered(self):
        """Return True if the BLE adapter is powered up, otherwise return False.
        """
        return IOBluetoothPreferenceGetControllerPowerState() == 1
