# Python objects to represent the bluez DBus GATT objects.  Provides properties
# and functions to easily interact with the DBus objects.
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
import uuid

import dbus

from ..interfaces import GattService, GattCharacteristic, GattDescriptor
from ..platform import get_provider


_SERVICE_INTERFACE        = 'org.bluez.GattService1'
_CHARACTERISTIC_INTERFACE = 'org.bluez.GattCharacteristic1'
_DESCRIPTOR_INTERFACE     = 'org.bluez.GattDescriptor1'


class BluezGattService(GattService):
    """Bluez GATT service object."""

    def __init__(self, dbus_obj):
        """Create an instance of the GATT service from the provided bluez
        DBus object.
        """
        self._props = dbus.Interface(dbus_obj, 'org.freedesktop.DBus.Properties')

    @property
    def uuid(self):
        """Return the UUID of this GATT service."""
        return uuid.UUID(str(self._props.Get(_SERVICE_INTERFACE, 'UUID')))

    def list_characteristics(self):
        """Return list of GATT characteristics that have been discovered for this
        service.
        """
        paths = self._props.Get(_SERVICE_INTERFACE, 'Characteristics')
        return map(BluezGattCharacteristic,
                   get_provider()._get_objects_by_path(paths))


class BluezGattCharacteristic(GattCharacteristic):
    """Bluez GATT characteristic object."""

    def __init__(self, dbus_obj):
        """Create an instance of the GATT characteristic from the provided bluez
        DBus object.
        """
        self._characteristic = dbus.Interface(dbus_obj, _CHARACTERISTIC_INTERFACE)
        self._props = dbus.Interface(dbus_obj, 'org.freedesktop.DBus.Properties')

    @property
    def uuid(self):
        """Return the UUID of this GATT characteristic."""
        return uuid.UUID(str(self._props.Get(_CHARACTERISTIC_INTERFACE, 'UUID')))

    def read_value(self):
        """Read the value of this characteristic."""
        return self._characteristic.ReadValue()

    def write_value(self, value):
        """Write the specified value to this characteristic."""
        self._characteristic.WriteValue(value)

    def start_notify(self, on_change):
        """Enable notification of changes for this characteristic on the
        specified on_change callback.  on_change should be a function that takes
        one parameter which is the value (as a string of bytes) of the changed
        characteristic value.
        """
        # Setup a closure to be the first step in handling the on change callback.
        # This closure will verify the characteristic is changed and pull out the
        # new value to pass to the user's on change callback.
        def characteristic_changed(iface, changed_props, invalidated_props):
            # Check that this change is for a GATT characteristic and it has a
            # new value.
            if iface != _CHARACTERISTIC_INTERFACE:
                return
            if 'Value' not in changed_props:
                return
            # Send the new value to the on_change callback.
            on_change(''.join(map(chr, changed_props['Value'])))
        # Hook up the property changed signal to call the closure above.
        self._props.connect_to_signal('PropertiesChanged', characteristic_changed)
        # Enable notifications for changes on the characteristic.
        self._characteristic.StartNotify()

    def stop_notify(self):
        """Disable notification of changes for this characteristic."""
        self._characteristic.StopNotify()

    def list_descriptors(self):
        """Return list of GATT descriptors that have been discovered for this
        characteristic.
        """
        paths = self._props.Get(_CHARACTERISTIC_INTERFACE, 'Descriptors')
        return map(BluezGattDescriptor,
                   get_provider()._get_objects_by_path(paths))


class BluezGattDescriptor(GattDescriptor):
    """Bluez GATT descriptor object."""

    def __init__(self, dbus_obj):
        """Create an instance of the GATT descriptor from the provided bluez
        DBus object.
        """
        self._descriptor = dbus.Interface(dbus_obj, _DESCRIPTOR_INTERFACE)
        self._props = dbus.Interface(dbus_obj, 'org.freedesktop.DBus.Properties')

    @property
    def uuid(self):
        """Return the UUID of this GATT descriptor."""
        return uuid.UUID(str(self._props.Get(_DESCRIPTOR_INTERFACE, 'UUID')))

    def read_value(self):
        """Read the value of this descriptor."""
        return self._descriptor.ReadValue()
