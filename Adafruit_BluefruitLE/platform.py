# Platform detection logic to pick the right BLE provider for the current
# platform.
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
import sys


# Keep a single global instance of the BLE provider.
_provider = None


def get_provider():
    """Return an instance of the BLE provider for the current platform."""
    global _provider
    # Set the provider based on the current platform.
    if _provider is None:
        if sys.platform.startswith('linux'):
            # Linux platform
            from .bluez_dbus.provider import BluezProvider
            _provider = BluezProvider()
        elif sys.platform == 'darwin':
            # Mac OSX platform
            from .corebluetooth.provider import CoreBluetoothProvider
            _provider = CoreBluetoothProvider()
        else:
            # Unsupported platform
            raise RuntimeError('Sorry the {0} platform is not supported by the BLE library!'.format(sys.platform))
    return _provider
