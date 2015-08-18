# Class that encapsulates access to a list of CoreBluetooth objects that are
# idenfitied by a NSUUID, like CBPeripherals (devices), CBCharacteristics, and
# CBDescriptors.
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


class CoreBluetoothMetadata(object):
    """Class that encapsulates access to metadata associated with CoreBluetooth
    objects like  CBPeripherals (devices), CBCharacteristics, and CBDescriptors.
    This is useful for associating extra state that isn't stored with Apple's
    classes, like callbacks to call, etc.  Think of this class as a dict that
    uses a CBDevice, CBPeripheral, etc. as the key and stores any object with
    that Objective-C type.  Care is taken to make access to the items thread safe
    so it can be accessed from multiple threads.
    """

    def __init__(self):
        # Initialize item dict and create a lock to synchronize access since it
        # will be manipulated by the main thread and user thread.
        self._metadata = {}
        self._lock = threading.Lock()

    def list(self):
        """Return list of all metadata objects."""
        with self._lock:
            return self._metadata.values()

    def get(self, cbobject):
        """Retrieve the metadata associated with the specified CoreBluetooth
        object.
        """
        with self._lock:
            return self._metadata.get(cbobject, None)

    def get_all(self, cbobjects):
        """Retrieve a list of metadata objects associated with the specified
        list of CoreBluetooth objects.  If an object cannot be found then an
        exception is thrown.
        """
        try:
            with self._lock:
                return [self._metadata[x] for x in cbobjects]
        except KeyError:
            # Note that if this error gets thrown then the assumption that OSX
            # will pass back to callbacks the exact CoreBluetooth objects that
            # were used previously is broken! (i.e. the CoreBluetooth objects
            # are not stateless)
            raise RuntimeError('Failed to find expected metadata for CoreBluetooth object!')

    def add(self, cbobject, metadata):
        """Add the specified CoreBluetooth item with the associated metadata if
        it doesn't already exist.  Returns the newly created or preexisting
        metadata item.
        """
        with self._lock:
            if cbobject not in self._metadata:
                self._metadata[cbobject] = metadata
            return self._metadata[cbobject]

    def remove(self, cbobject):
        """Remove any metadata associated with the provided CoreBluetooth object.
        """
        with self._lock:
            if cbobject in self._metadata:
                del self._metadata[cbobject]
