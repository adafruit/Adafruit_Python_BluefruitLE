# Python object to represent the bluez DBus adapter object.  Provides properties
# and functions to easily interact with the DBus object.
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
import threading

import dbus

from ..config import TIMEOUT_SEC
from ..interfaces import Adapter


_INTERFACE = 'org.bluez.Adapter1'


class BluezAdapter(Adapter):
    """Bluez BLE network adapter."""

    def __init__(self, dbus_obj):
        """Create an instance of the bluetooth adapter from the provided bluez
        DBus object.
        """
        self._adapter = dbus.Interface(dbus_obj, _INTERFACE)
        self._props = dbus.Interface(dbus_obj, 'org.freedesktop.DBus.Properties')
        self._scan_started = threading.Event()
        self._scan_stopped = threading.Event()
        self._props.connect_to_signal('PropertiesChanged', self._prop_changed)

    def _prop_changed(self, iface, changed_props, invalidated_props):
        # Handle property changes for the adapter.  Note this call happens in
        # a separate thread so be careful to make thread safe changes to state!
        # Skip any change events not for this adapter interface.
        if iface != _INTERFACE:
            return
        # If scanning starts then fire the scan started event.
        if 'Discovering' in changed_props and changed_props['Discovering'] == 1:
            self._scan_started.set()
        # If scanning stops then fire the scan stopped event.
        if 'Discovering' in changed_props and changed_props['Discovering'] == 0:
            self._scan_stopped.set()

    @property
    def name(self):
        """Return the name of this BLE network adapter."""
        return self._props.Get(_INTERFACE, 'Name')

    def start_scan(self, timeout_sec=TIMEOUT_SEC):
        """Start scanning for BLE devices with this adapter."""
        self._scan_started.clear()
        self._adapter.StartDiscovery()
        if not self._scan_started.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting for adapter to start scanning!')

    def stop_scan(self, timeout_sec=TIMEOUT_SEC):
        """Stop scanning for BLE devices with this adapter."""
        self._scan_stopped.clear()
        self._adapter.StopDiscovery()
        if not self._scan_stopped.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting for adapter to stop scanning!')

    @property
    def is_scanning(self):
        """Return True if the BLE adapter is scanning for devices, otherwise
        return False.
        """
        return self._props.Get(_INTERFACE, 'Discovering')

    def power_on(self):
        """Power on this BLE adapter."""
        return self._props.Set(_INTERFACE, 'Powered', True)

    def power_off(self):
        """Power off this BLE adapter."""
        return self._props.Set(_INTERFACE, 'Powered', False)

    @property
    def is_powered(self):
        """Return True if the BLE adapter is powered up, otherwise return False.
        """
        return self._props.Get(_INTERFACE, 'Powered')
