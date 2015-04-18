# Bluetooth LE UART service class.  Provides an easy to use interface to read
# and write data from a bluezle device that implements the UART service.
# Author: Tony DiCola
import Queue
import uuid

from ..bluezle_dbus import bluez, GattCharacteristic, ServiceBase


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
        self._queue = Queue.Queue()
        # Find the RX and TX characteristics.
        chars = map(GattCharacteristic,
                    bluez.get_objects('org.bluez.GattCharacteristic1',
                                      device.object_path))
        self._tx = filter(lambda x: x.uuid == TX_CHAR_UUID, chars)[0]
        self._rx = filter(lambda x: x.uuid == RX_CHAR_UUID, chars)[0]
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

    def read(self, timeout_sec=None):
        """Block until data is available to read from the UART.  Will return a
        string of data that has been received.  Timeout_sec specifies how many
        seconds to wait for data to be available and will block forever if None
        (the default).  If the timeout is exceeded and no data is found then
        None is returned.
        """
        try:
            return self._queue.get(timeout=timeout_sec)
        except Queue.Empty:
            # Timeout exceeded, return None to signify no data received.
            return None
