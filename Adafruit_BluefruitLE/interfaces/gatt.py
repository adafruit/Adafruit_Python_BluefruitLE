# Base classes for BLE GATT services, characteristics, and descriptors.  Each
# OS supported by the library should inherit from these classes and implement
# the abstract methods.
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
import abc


class GattService(object):
    """Base class for a BLE GATT service."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def uuid(self):
        """Return the UUID of this GATT service."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_characteristics(self):
        """Return list of GATT characteristics that have been discovered for this
        service.
        """
        raise NotImplementedError

    def find_characteristic(self, uuid):
        """Return the first child characteristic found that has the specified
        UUID.  Will return None if no characteristic that matches is found.
        """
        for char in self.list_characteristics():
            if char.uuid == uuid:
                return char
        return None


class GattCharacteristic(object):
    """Base class for a BLE GATT characteristic."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def uuid(self):
        """Return the UUID of this GATT characteristic."""
        raise NotImplementedError

    @abc.abstractmethod
    def read_value(self):
        """Read the value of this characteristic."""
        raise NotImplementedError

    @abc.abstractmethod
    def write_value(self, value):
        """Write the specified value to this characteristic."""
        raise NotImplementedError

    @abc.abstractmethod
    def start_notify(self, on_change):
        """Enable notification of changes for this characteristic on the
        specified on_change callback.  on_change should be a function that takes
        one parameter which is the value (as a string of bytes) of the changed
        characteristic value.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def stop_notify(self):
        """Disable notification of changes for this characteristic."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_descriptors(self):
        """Return list of GATT descriptors that have been discovered for this
        characteristic.
        """
        raise NotImplementedError

    def find_descriptor(self, uuid):
        """Return the first child descriptor found that has the specified
        UUID.  Will return None if no descriptor that matches is found.
        """
        for desc in self.list_descriptors():
            if desc.uuid == uuid:
                return desc
        return None


class GattDescriptor(object):
    """Base class for a BLE GATT descriptor."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def uuid(self):
        """Return the UUID of this GATT descriptor."""
        raise NotImplementedError

    @abc.abstractmethod
    def read_value(self):
        """Read the value of this descriptor."""
        raise NotImplementedError
