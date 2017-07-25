# Base class for a BLE provider.  Each OS supported by the library should
# inherit from this class and implement the abstract methods, then update the
# platform.py code to detect when the platform is present and use the
# implementation of this provider base class.
# Author: Tony DiCola
#
# Note that platform.py will ensure only once instance of this class ever exists
# so it is safe to make assumptions that there are not multiple instances.
#
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
import time

from ..config import TIMEOUT_SEC


class Provider(object):
    """Base class for a BLE provider."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def initialize(self):
        """Initialize the BLE provider.  Must be called once before any other
        calls are made to the provider.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def run_mainloop_with(self, target):
        """Start the OS's main loop to process asyncronous BLE events and then
        run the specified target function in a background thread.  Target
        function should be a function that takes no parameters and optionally
        return an integer response code.  When the target function stops
        executing or returns with value then the main loop will be stopped and
        the program will exit with the returned code.

        Note that an OS main loop is required to process asyncronous BLE events
        and this function is provided as a convenience for writing simple tools
        and scripts that don't need to be full-blown GUI applications.  If you
        are writing a GUI application that has a main loop (a GTK glib main loop
        on Linux, or a Cocoa main loop on OSX) then you don't need to call this
        function.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list_adapters(self):
        """Return a list of BLE adapter objects connected to the system."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_devices(self):
        """Return a list of BLE devices known to the system."""
        raise NotImplementedError

    @abc.abstractmethod
    def clear_cached_data(self):
        """Clear any internally cached BLE device data.  Necessary in some cases
        to prevent issues with stale device data getting cached by the OS.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def disconnect_devices(self, service_uuids):
        """Disconnect any connected devices that have any of the specified
        service UUIDs.
        """
        raise NotImplementedError

    def get_default_adapter(self):
        """Return the first BLE adapter found, or None if no adapters are
        available.
        """
        adapters = self.list_adapters()
        if len(adapters) > 0:
            return adapters[0]
        else:
            return None

    def find_devices(self, service_uuids=[], name=None):
        """Return devices that advertise the specified service UUIDs and/or have
        the specified name.  Service_uuids should be a list of Python uuid.UUID
        objects and is optional.  Name is a string device name to look for and is
        also optional.  Will not block, instead it returns immediately with a
        list of found devices (which might be empty).
        """
        # Convert service UUID list to counter for quicker comparison.
        expected = set(service_uuids)
        # Grab all the devices.
        devices = self.list_devices()
        # Filter to just the devices that have the requested service UUID/name.
        found = []
        for device in devices:
            if name is not None:
                if device.name == name:
                    # Check if the name matches and add the device.
                    found.append(device)
            else:
                # Check if the advertised UUIDs have at least the expected UUIDs.
                actual = set(device.advertised)
                if actual >= expected:
                    found.append(device)
        return found


    def find_device(self, service_uuids=[], name=None, timeout_sec=TIMEOUT_SEC):
        """Return the first device that advertises the specified service UUIDs or
        has the specified name. Will wait up to timeout_sec seconds for the device
        to be found, and if the timeout is zero then it will not wait at all and
        immediately return a result.  When no device is found a value of None is
        returned.
        """
        start = time.time()
        while True:
            # Call find_devices and grab the first result if any are found.
            found = self.find_devices(service_uuids, name)
            if len(found) > 0:
                return found[0]
            # No device was found.  Check if the timeout is exceeded and wait to
            # try again.
            if time.time()-start >= timeout_sec:
                # Failed to find a device within the timeout.
                return None
            time.sleep(1)
