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
import abc


class Adapter(object):
    """Base class for a BLE network adapter."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def name(self):
        """Return the name of this BLE network adapter."""
        raise NotImplementedError

    @abc.abstractmethod
    def start_scan(self, timeout_sec):
        """Start scanning for BLE devices with this adapter."""
        raise NotImplementedError

    @abc.abstractmethod
    def stop_scan(self, timeout_sec):
        """Stop scanning for BLE devices with this adapter."""
        raise NotImplementedError

    @abc.abstractproperty
    def is_scanning(self):
        """Return True if the BLE adapter is scanning for devices, otherwise
        return False.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def power_on(self):
        """Power on this BLE adapter."""
        raise NotImplementedError

    @abc.abstractmethod
    def power_off(self):
        """Power off this BLE adapter."""
        raise NotImplementedError

    @abc.abstractproperty
    def is_powered(self):
        """Return True if the BLE adapter is powered up, otherwise return False.
        """
        raise NotImplementedError
