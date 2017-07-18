# Base class for a BLE network adapter.  Each OS supported by the library should
# inherit from this class and implement the abstract methods.
# Author: Tony DiCola
#
# Copyright (c) 2015 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import logging
import threading
import time

import objc

from ..config import TIMEOUT_SEC
from ..interfaces import Adapter
from ..platform import get_provider


# Load IOBluetooth functions for controlling bluetooth power state.
objc.loadBundleFunctions(
    objc.loadBundle("IOBluetooth", globals(), bundle_path=objc.pathForFramework(u'/System/Library/Frameworks/IOBluetooth.framework')),
    globals(),
    [('IOBluetoothPreferenceGetControllerPowerState', b'oI'),('IOBluetoothPreferenceSetControllerPowerState', b'vI')]
)

logger = logging.getLogger(__name__)


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
        self._powered_on = threading.Event()
        self._powered_off = threading.Event()

    def _state_changed(self, state):
        """Called when the power state changes."""
        logger.debug('Adapter state change: {0}'.format(state))
        # Handle when powered on.
        if state == 5:
            self._powered_off.clear()
            self._powered_on.set()
        # Handle when powered off.
        elif state == 4:
            self._powered_on.clear()
            self._powered_off.set()

    @property
    def name(self):
        """Return the name of this BLE network adapter."""
        # Mac OSX has no oncept of BLE adapters so just return a fixed value.
        return "Default Adapter"

    def start_scan(self, timeout_sec=TIMEOUT_SEC):
        """Start scanning for BLE devices."""
        get_provider()._central_manager.scanForPeripheralsWithServices_options_(None, None)
        self._is_scanning = True

    def stop_scan(self, timeout_sec=TIMEOUT_SEC):
        """Stop scanning for BLE devices."""
        get_provider()._central_manager.stopScan()
        self._is_scanning = False

    @property
    def is_scanning(self):
        """Return True if the BLE adapter is scanning for devices, otherwise
        return False.
        """
        return self._is_scanning

    def power_on(self, timeout_sec=TIMEOUT_SEC):
        """Power on Bluetooth."""
        # Turn on bluetooth and wait for powered on event to be set.
        self._powered_on.clear()
        IOBluetoothPreferenceSetControllerPowerState(1)
        if not self._powered_on.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting for adapter to power on!')

    def power_off(self, timeout_sec=TIMEOUT_SEC):
        """Power off Bluetooth."""
        # Turn off bluetooth.
        self._powered_off.clear()
        IOBluetoothPreferenceSetControllerPowerState(0)
        if not self._powered_off.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting for adapter to power off!')

    @property
    def is_powered(self):
        """Return True if the BLE adapter is powered up, otherwise return False.
        """
        return IOBluetoothPreferenceGetControllerPowerState() == 1
