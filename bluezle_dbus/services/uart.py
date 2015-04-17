# Bluetooth LE UART service class.  Provides an easy to use interface to read
# and write data from a bluezle device that implements the UART service.
# Author: Tony DiCola
import Queue
import uuid

from .. import bluez
from ..gatt import GattCharacteristic

# Define service and characteristic UUIDs.
UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')


class UART(object):
    """Bluetooth LE UART service object."""

    def __init__(self, device):
        """Initialize UART from provided bluez device."""
        self._queue = Queue.Queue()
        # Check that the device implements the UART service.
        found = False
        for dev_uuid in device.uuids:
            if uuid.UUID(str(dev_uuid)) == UART_SERVICE_UUID:
                found = True
                break
        if not found:
            raise RuntimeError('Device does not implement UART service!')
        # Find the RX and TX characteristics.
        chars = map(GattCharacteristic, bluez.get_objects('org.bluez.GattCharacteristic1'))
        tx_char = filter(lambda x: uuid.UUID(str(x.uuid)) == TX_CHAR_UUID, chars)
        rx_char = filter(lambda x: uuid.UUID(str(x.uuid)) == RX_CHAR_UUID, chars)
        if len(tx_char) != 1 or len(rx_char) != 1:
            raise RuntimeError('Device does not implement a single RX/TX characteristic!')
        self._tx = tx_char[0]
        self._rx = rx_char[0]
        # Subscribe to rx characteristic changes to receive data.
        self._rx._props.connect_to_signal('PropertiesChanged', self._rx_received)
        self._rx.start_notify()

    def _rx_received(self, iface, changed_props, invalidated_props):
        # Stop if this event isn't for a GATT characteristic value update.
        if iface != 'org.bluez.GattCharacteristic1':
            return
        if 'Value' not in changed_props:
            return
        # Grab the bytes of the message.
        message = changed_props['Value']
        # Convert bytes to string and put them in the queue to be available for
        # reading on the main program thread (this callback is called on the
        # GLib main loop so it's dangerous to do much other processing).
        self._queue.put(''.join(map(chr, message)))

    def write(self, data):
        """Write a string of data to the UART device."""
        self._tx.write_value(data)

    def read(self):
        """Block until data is available to read from the UART.  Will return a
        string of data that has been received.
        """
        return self._queue.get()
