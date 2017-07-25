# Bluetooth LE UART service class.  Provides an easy to use interface to read
# and write data from a bluezle device that implements the UART service.
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
import queue
import uuid

from .servicebase import ServiceBase


# Define service and characteristic UUIDs.
UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')


class UART(ServiceBase):
    """Bluetooth LE UART service object."""

    # Configure expected services and characteristics for the UART service.
    ADVERTISED = [UART_SERVICE_UUID]
    SERVICES = [UART_SERVICE_UUID]
    CHARACTERISTICS = [TX_CHAR_UUID, RX_CHAR_UUID]

    def __init__(self, device):
        """Initialize UART from provided bluez device."""
        # Find the UART service and characteristics associated with the device.
        self._uart = device.find_service(UART_SERVICE_UUID)
        if self._uart is None:
            raise RuntimeError('Failed to find expected UART service!')
        self._tx = self._uart.find_characteristic(TX_CHAR_UUID)
        self._rx = self._uart.find_characteristic(RX_CHAR_UUID)
        if self._tx is None or self._rx is None:
            raise RuntimeError('Failed to find expected UART RX and TX characteristics!')
        # Use a queue to pass data received from the RX property change back to
        # the main thread in a thread-safe way.
        self._queue = queue.Queue()
        # Subscribe to RX characteristic changes to receive data.
        self._rx.start_notify(self._rx_received)

    def _rx_received(self, data):
        # Callback that's called when data is received on the RX characteristic.
        # Just throw the new data in the queue so the read function can access
        # it on the main thread.
        self._queue.put(data)

    def write(self, data):
        """Write a string of data to the UART device."""
        self._tx.write_value(data)

    def read(self, timeout_sec=None):
        """Block until data is available to read from the UART.  Will return a
        string of data that has been received.  Timeout_sec specifies how many
        seconds to wait for data to be available and will block forever if None
        (the default).  If the timeout is exceeded and no data is found then
        None is returned.
        """
        try:
            return self._queue.get(timeout=timeout_sec)
        except queue.Empty:
            # Timeout exceeded, return None to signify no data received.
            return None
