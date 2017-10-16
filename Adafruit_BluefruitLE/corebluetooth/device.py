# Python object to represent the CoreBluetooth device object.
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

from ..config import TIMEOUT_SEC
from ..interfaces import Device
from ..platform import get_provider

from .gatt import CoreBluetoothGattService
from .objc_helpers import cbuuid_to_uuid, nsuuid_to_uuid
from .provider import device_list, service_list, characteristic_list, descriptor_list


class CoreBluetoothDevice(Device):
    """CoreBluetooth BLE device."""

    def __init__(self, peripheral):
        """Create an instance of the CoreBluetooth device from the provided
        CBPeripheral instance.
        """
        self._peripheral = peripheral
        self._advertised = []
        self._discovered_services = set()
        self._char_on_changed = {}
        self._rssi = None
        # Events to signify when an asyncronous request has finished.
        self._connected = threading.Event()
        self._disconnected = threading.Event()
        self._discovered = threading.Event()
        self._rssi_read = threading.Event()

    @property
    def _central_manager(self):
        # Lookup the CBCentralManager, reduces verbosity of calls.
        return get_provider()._central_manager

    def connect(self, timeout_sec=TIMEOUT_SEC):
        """Connect to the device.  If not connected within the specified timeout
        then an exception is thrown.
        """
        self._central_manager.connectPeripheral_options_(self._peripheral, None)
        if not self._connected.wait(timeout_sec):
            raise RuntimeError('Failed to connect to device within timeout period!')

    def disconnect(self, timeout_sec=TIMEOUT_SEC):
        """Disconnect from the device.  If not disconnected within the specified
        timeout then an exception is thrown.
        """
        # Remove all the services, characteristics, and descriptors from the
        # lists of those items.  Do this before disconnecting because they wont't
        # be accessible afterwards.
        for service in self.list_services():
            for char in service.list_characteristics():
                for desc in char.list_descriptors():
                    descriptor_list().remove(desc)
                characteristic_list().remove(char)
            service_list().remove(service)
        # Now disconnect.
        self._central_manager.cancelPeripheralConnection_(self._peripheral)
        if not self._disconnected.wait(timeout_sec):
            raise RuntimeError('Failed to disconnect to device within timeout period!')

    def _set_connected(self):
        """Set the connected event."""
        self._disconnected.clear()
        self._connected.set()

    def _set_disconnected(self):
        """Set the connected event."""
        self._connected.clear()
        self._disconnected.set()

    def _update_advertised(self, advertised):
        """Called when advertisement data is received."""
        # Advertisement data was received, pull out advertised service UUIDs and
        # name from advertisement data.
        if 'kCBAdvDataServiceUUIDs' in advertised:
            self._advertised = self._advertised + map(cbuuid_to_uuid, advertised['kCBAdvDataServiceUUIDs'])

    def _characteristics_discovered(self, service):
        """Called when GATT characteristics have been discovered."""
        # Characteristics for the specified service were discovered.  Update
        # set of discovered services and signal when all have been discovered.
        self._discovered_services.add(service)
        if self._discovered_services >= set(self._peripheral.services()):
            # Found all the services characteristics, finally time to fire the
            # service discovery complete event.
            self._discovered.set()

    def _notify_characteristic(self, characteristic, on_change):
        """Call the specified on_change callback when this characteristic
        changes.
        """
        # Associate the specified on_changed callback with any changes to this
        # characteristic.
        self._char_on_changed[characteristic] = on_change

    def _characteristic_changed(self, characteristic):
        """Called when the specified characteristic has changed its value."""
        # Called when a characteristic is changed.  Get the on_changed handler
        # for this characteristic (if it exists) and call it.
        on_changed = self._char_on_changed.get(characteristic, None)
        if on_changed is not None:
            on_changed(characteristic.value().bytes().tobytes())
        # Also tell the characteristic that it has a new value.
        # First get the service that is associated with this characteristic.
        char = characteristic_list().get(characteristic)
        if char is not None:
            char._value_read.set()

    def _descriptor_changed(self, descriptor):
        """Called when the specified descriptor has changed its value."""
        # Tell the descriptor it has a new value to read.
        desc = descriptor_list().get(descriptor)
        if desc is not None:
            desc._value_read.set()

    def _rssi_changed(self, rssi):
        """Called when the RSSI signal strength has been read."""
        self._rssi = rssi
        self._rssi_read.set()

    def list_services(self):
        """Return a list of GattService objects that have been discovered for
        this device.
        """
        return service_list().get_all(self._peripheral.services())

    def discover(self, service_uuids, char_uuids, timeout_sec=TIMEOUT_SEC):
        """Wait up to timeout_sec for the specified services and characteristics
        to be discovered on the device.  If the timeout is exceeded without
        discovering the services and characteristics then an exception is thrown.
        """
        # Since OSX tells us when all services and characteristics are discovered
        # this function can just wait for that full service discovery.
        if not self._discovered.wait(timeout_sec):
            raise RuntimeError('Failed to discover device services within timeout period!')

    @property
    def advertised(self):
        """Return a list of UUIDs for services that are advertised by this
        device.
        """
        return self._advertised

    @property
    def id(self):
        """Return a unique identifier for this device.  On supported platforms
        this will be the MAC address of the device, however on unsupported
        platforms (Mac OSX) it will be a unique ID like a UUID.
        """
        return nsuuid_to_uuid(self._peripheral.identifier())

    @property
    def name(self):
        """Return the name of this device."""
        return self._peripheral.name()

    @property
    def is_connected(self):
        """Return True if the device is connected to the system, otherwise False.
        """
        return self._connected.is_set()

    @property
    def rssi(self, timeout_sec=TIMEOUT_SEC):
        """Return the RSSI signal strength in decibels."""
        # Kick off query to get RSSI, then wait for it to return asyncronously
        # when the _rssi_changed() function is called.
        self._rssi_read.clear()
        self._peripheral.readRSSI()
        if not self._rssi_read.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting for RSSI value!')
        return self._rssi
