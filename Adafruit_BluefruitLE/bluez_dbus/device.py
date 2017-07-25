# Python object to represent the bluez DBus device object.  Provides properties
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
from past.builtins import map
import threading
import time
import uuid

import dbus

from ..config import TIMEOUT_SEC
from ..interfaces import Device
from ..platform import get_provider

from .adapter import _INTERFACE as _ADAPTER_INTERFACE
from .gatt import BluezGattService, BluezGattCharacteristic, _SERVICE_INTERFACE, _CHARACTERISTIC_INTERFACE


_INTERFACE = 'org.bluez.Device1'


class BluezDevice(Device):
    """Bluez BLE device."""

    def __init__(self, dbus_obj):
        """Create an instance of the bluetooth device from the provided bluez
        DBus object.
        """
        self._device = dbus.Interface(dbus_obj, _INTERFACE)
        self._props = dbus.Interface(dbus_obj, 'org.freedesktop.DBus.Properties')
        self._connected = threading.Event()
        self._disconnected = threading.Event()
        self._props.connect_to_signal('PropertiesChanged', self._prop_changed)

    def _prop_changed(self, iface, changed_props, invalidated_props):
        # Handle property changes for the device.  Note this call happens in
        # a separate thread so be careful to make thread safe changes to state!
        # Skip any change events not for this adapter interface.
        if iface != _INTERFACE:
            return
        # If connected then fire the connected event.
        if 'Connected' in changed_props and changed_props['Connected'] == 1:
            self._connected.set()
        # If disconnected then fire the disconnected event.
        if 'Connected' in changed_props and changed_props['Connected'] == 0:
            self._disconnected.set()

    def connect(self, timeout_sec=TIMEOUT_SEC):
        """Connect to the device.  If not connected within the specified timeout
        then an exception is thrown.
        """
        self._connected.clear()
        self._device.Connect()
        if not self._connected.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting to connect to device!')

    def disconnect(self, timeout_sec=TIMEOUT_SEC):
        """Disconnect from the device.  If not disconnected within the specified
        timeout then an exception is thrown.
        """
        self._disconnected.clear()
        self._device.Disconnect()
        if not self._disconnected.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting to disconnect from device!')

    def list_services(self):
        """Return a list of GattService objects that have been discovered for
        this device.
        """
        return map(BluezGattService,
                   get_provider()._get_objects(_SERVICE_INTERFACE,
                                               self._device.object_path))

    def discover(self, service_uuids, char_uuids, timeout_sec=TIMEOUT_SEC):
        """Wait up to timeout_sec for the specified services and characteristics
        to be discovered on the device.  If the timeout is exceeded without
        discovering the services and characteristics then an exception is thrown.
        """
        # Turn expected values into a counter of each UUID for fast comparison.
        expected_services = set(service_uuids)
        expected_chars = set(char_uuids)
        # Loop trying to find the expected services for the device.
        start = time.time()
        while True:
            # Find actual services discovered for the device.
            actual_services = set(self.advertised)
            # Find actual characteristics discovered for the device.
            chars = map(BluezGattCharacteristic,
                        get_provider()._get_objects(_CHARACTERISTIC_INTERFACE,
                                                    self._device.object_path))
            actual_chars = set(map(lambda x: x.uuid, chars))
            # Compare actual discovered UUIDs with expected and return true if at
            # least the expected UUIDs are available.
            if actual_services >= expected_services and actual_chars >= expected_chars:
                # Found at least the expected services!
                return True
            # Couldn't find the devices so check if timeout has expired and try again.
            if time.time()-start >= timeout_sec:
                return False
            time.sleep(1)

    @property
    def advertised(self):
        """Return a list of UUIDs for services that are advertised by this
        device.
        """
        uuids = []
        # Get UUIDs property but wrap it in a try/except to catch if the property
        # doesn't exist as it is optional.
        try:
            uuids = self._props.Get(_INTERFACE, 'UUIDs')
        except dbus.exceptions.DBusException as ex:
            # Ignore error if device has no UUIDs property (i.e. might not be
            # a BLE device).
            if ex.get_dbus_name() != 'org.freedesktop.DBus.Error.InvalidArgs':
                raise ex
        return [uuid.UUID(str(x)) for x in uuids]

    @property
    def id(self):
        """Return a unique identifier for this device.  On supported platforms
        this will be the MAC address of the device, however on unsupported
        platforms (Mac OSX) it will be a unique ID like a UUID.
        """
        return self._props.Get(_INTERFACE, 'Address')

    @property
    def name(self):
        """Return the name of this device."""
        return self._props.Get(_INTERFACE, 'Name')

    @property
    def is_connected(self):
        """Return True if the device is connected to the system, otherwise False.
        """
        return self._props.Get(_INTERFACE, 'Connected')

    @property
    def rssi(self):
        """Return the RSSI signal strength in decibels."""
        return self._props.Get(_INTERFACE, 'RSSI')

    @property
    def _adapter(self):
        """Return the DBus path to the adapter that owns this device."""
        return self._props.Get(_INTERFACE, 'Adapter')
