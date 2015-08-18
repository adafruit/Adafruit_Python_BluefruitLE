# Python objects to represent the CoreBluetooth GATT objects.
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

import objc

from ..config import TIMEOUT_SEC
from ..interfaces import GattService, GattCharacteristic, GattDescriptor

from .objc_helpers import cbuuid_to_uuid
from .provider import device_list, characteristic_list, descriptor_list


# Load CoreBluetooth bundle.
objc.loadBundle("CoreBluetooth", globals(),
    bundle_path=objc.pathForFramework(u'/System/Library/Frameworks/IOBluetooth.framework/Versions/A/Frameworks/CoreBluetooth.framework'))


class CoreBluetoothGattService(GattService):
    """CoreBluetooth GATT service object."""

    def __init__(self, service):
        """Create an instance of the GATT service from the provided CoreBluetooth
        CBService instance.
        """
        self._service = service

    @property
    def uuid(self):
        """Return the UUID of this GATT service."""
        return cbuuid_to_uuid(self._service.UUID())

    def list_characteristics(self):
        """Return list of GATT characteristics that have been discovered for this
        service.
        """
        # Get the CoreBluetoothGattCharacteristic objects cached in the provider
        # for this service's characteristics.
        return characteristic_list().get_all(self._service.characteristics())


class CoreBluetoothGattCharacteristic(GattCharacteristic):
    """CoreBluetooth GATT characteristic object."""

    def __init__(self, characteristic):
        """Create an instance of the GATT characteristic from the provided
        CoreBluetooth CBCharacteristic instance.
        """
        self._characteristic = characteristic
        self._value_read = threading.Event()

    @property
    def _device(self):
        """Return the parent CoreBluetoothDevice object that owns this
        characteristic.
        """
        return device_list().get(self._characteristic.service().peripheral())

    @property
    def uuid(self):
        """Return the UUID of this GATT characteristic."""
        return cbuuid_to_uuid(self._characteristic.UUID())

    def read_value(self, timeout_sec=TIMEOUT_SEC):
        """Read the value of this characteristic."""
        # Kick off a query to read the value of the characteristic, then wait
        # for the result to return asyncronously.
        self._value_read.clear()
        self._device._peripheral.readValueForCharacteristic_(self._characteristic)
        if not self._value_read.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting to read characteristic value!')
        return self._characteristic.value()

    def write_value(self, value, write_type=0):
        """Write the specified value to this characteristic."""
        data = NSData.dataWithBytes_length_(value, len(value))
        self._device._peripheral.writeValue_forCharacteristic_type_(data,
            self._characteristic,
            write_type)

    def start_notify(self, on_change):
        """Enable notification of changes for this characteristic on the
        specified on_change callback.  on_change should be a function that takes
        one parameter which is the value (as a string of bytes) of the changed
        characteristic value.
        """
        # Tell the device what callback to use for changes to this characteristic.
        self._device._notify_characteristic(self._characteristic, on_change)
        # Turn on notifications of characteristic changes.
        self._device._peripheral.setNotifyValue_forCharacteristic_(True,
            self._characteristic)

    def stop_notify(self):
        """Disable notification of changes for this characteristic."""
        self._device._peripheral.setNotifyValue_forCharacteristic_(False,
            self._characteristic)

    def list_descriptors(self):
        """Return list of GATT descriptors that have been discovered for this
        characteristic.
        """
        # Get the CoreBluetoothGattDescriptor objects cached in the provider
        # for this characteristics's descriptors.
        return descriptor_list().get_all(self._characteristic.descriptors())


class CoreBluetoothGattDescriptor(GattDescriptor):
    """CoreBluetooth GATT descriptor object."""

    def __init__(self, descriptor):
        """Create an instance of the GATT descriptor from the provided
        CoreBluetooth CBDescriptor value.
        """
        self._descriptor = descriptor
        self._value_read = threading.Event()

    @property
    def _device(self):
        """Return the parent CoreBluetoothDevice object that owns this
        characteristic.
        """
        return device_list().get(self._descriptor.characteristic().service().peripheral())

    @property
    def uuid(self):
        """Return the UUID of this GATT descriptor."""
        return cbuuid_to_uuid(self._descriptor.UUID())

    def read_value(self):
        """Read the value of this descriptor."""
        pass
        # Kick off a query to read the value of the descriptor, then wait
        # for the result to return asyncronously.
        self._value_read.clear()
        self._device._peripheral.readValueForDescriptor(self._descriptor)
        if not self._value_read.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting to read characteristic value!')
        return self._value
