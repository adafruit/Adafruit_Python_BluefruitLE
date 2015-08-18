# Bluetooth LE service base class.  Provides functions to simplify and decouple
# service implementations from specific BLE implementations.
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
from ..config import TIMEOUT_SEC
from ..platform import get_provider


class ServiceBase(object):
    """Base class for Bluetooth LE service classes.  Derived classes should
    have these class-level attributes:
      - ADVERTISED: List of expected service UUIDs for advertised devices.
      - SERVICES: List of expected service UUIDs (includes advertised and
                  unadvertised services).
      - CHARACTERISTICS: List of expected characteristic UUIDs.
    """

    @classmethod
    def find_device(cls, timeout_sec=TIMEOUT_SEC):
        """Find the first available device that supports this service and return
        it, or None if no device is found.  Will wait for up to timeout_sec
        seconds to find the device.
        """
        return get_provider().find_device(service_uuids=cls.ADVERTISED, timeout_sec=timeout_sec)

    @classmethod
    def find_devices(cls):
        """Find all the available devices that support this service and
        returns a list of them.  Does not poll and will return immediately.
        """
        return get_provider().find_devices(cls.ADVERTISED)

    @classmethod
    def disconnect_devices(cls):
        """Disconnect any currently connected devices that implement this
        service.
        """
        return get_provider().disconnect_devices(service_uuids=cls.ADVERTISED)

    @classmethod
    def discover(cls, device, timeout_sec=TIMEOUT_SEC):
        """Wait until the specified device has discovered the expected services
        and characteristics for this service.  Should be called once before other
        calls are made on the service.  Returns true if the service has been
        discovered in the specified timeout, or false if not discovered.
        """
        device.discover(cls.SERVICES, cls.CHARACTERISTICS, timeout_sec)
