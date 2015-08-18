# Smart Bulb Colorific! service class.  Provides control of a BLE RGB light bulb.
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
import uuid

from .servicebase import ServiceBase


# Define service and characteristic UUIDs.
COLOR_SERVICE_UUID = uuid.UUID('00001802-0000-1000-8000-00805f9b34fb')
COLOR_CHAR_UUID    = uuid.UUID('00002a06-0000-1000-8000-00805f9b34fb')


class Colorific(ServiceBase):
    """Smart Bulb Colorific! service object."""

    # Configure expected services and characteristics.
    ADVERTISED = [COLOR_SERVICE_UUID]
    SERVICES = [COLOR_SERVICE_UUID]
    CHARACTERISTICS = [COLOR_CHAR_UUID]

    def __init__(self, device):
        """Initialize device information from provided bluez device."""
        # Get the color characteristic.
        self._colorific = device.find_service(COLOR_SERVICE_UUID)
        self._color = self._colorific.find_characteristic(COLOR_CHAR_UUID)

    def set_color(self, r, g, b):
        """Set the red, green, blue color of the bulb."""
        # See more details on the bulb's protocol from this guide:
        #   https://learn.adafruit.com/reverse-engineering-a-bluetooth-low-energy-light-bulb/overview
        command = '\x58\x01\x03\x01\xFF\x00{0}{1}{2}'.format(chr(r & 0xFF),
                                                             chr(g & 0xFF),
                                                             chr(b & 0xFF))
        self._color.write_value(command)
