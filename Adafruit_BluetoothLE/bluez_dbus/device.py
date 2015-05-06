# Python object to represent the bluez DBus device object.  Provides properties
# and functions to easily interact with the DBus object.
# Author: Tony DiCola
from collections import Counter
import threading
import time
import uuid

import dbus

from ..interfaces import Device
from ..platform import get_provider

from .adapter import _INTERFACE as _ADAPTER_INTERFACE
from .gatt import BluezGattService, BluezGattCharacteristic, _SERVICE_INTERFACE, _CHARACTERISTIC_INTERFACE


_INTERFACE = 'org.bluez.Device1'


class BluezDevice(Device):
    """Bluez BLE device."""

    def __init__(self, dbus_obj):
        """Create an instance of the bluetooth device from the provided bluez
        DBus object.
        """
        self._device = dbus.Interface(dbus_obj, _INTERFACE)
        self._props = dbus.Interface(dbus_obj, 'org.freedesktop.DBus.Properties')
        self._connected = threading.Event()
        self._disconnected = threading.Event()
        self._props.connect_to_signal('PropertiesChanged', self._prop_changed)

    def _prop_changed(self, iface, changed_props, invalidated_props):
        # Handle property changes for the device.  Note this call happens in
        # a separate thread so be careful to make thread safe changes to state!
        # Skip any change events not for this adapter interface.
        if iface != _INTERFACE:
            return
        # If connected then fire the connected event.
        if 'Connected' in changed_props and changed_props['Connected'] == 1:
            self._connected.set()
        # If disconnected then fire the disconnected event.
        if 'Connected' in changed_props and changed_props['Connected'] == 0:
            self._disconnected.set()

    def connect(self, timeout_sec=30):
        """Connect to the device.  If not connected within the specified timeout
        then an exception is thrown.
        """
        self._connected.clear()
        self._device.Connect()
        if not self._connected.wait(timeout_sec):
            raise RuntimeError('Exceeded timeout waiting to connect to device!')

    def disconnect(self, timeout_sec=30):
        """Disconnect from the device.  If not disconnected within the specified
        timeout then an exception is thrown.
        """
        self._disconnected.clear()
        self._device.Disconnect()
        if self._disconnected.wait(timeout_sec):
            # Remove this device to work around an issue where bluez will change
            # the uuid list for a disconnected device.  
            # First get the adapter associated with the device.
            adapter = dbus.Interface(get_provider()._bus.get_object('org.bluez', self._adapter),
                                     _ADAPTER_INTERFACE)
            # Now call RemoveDevice on the adapter to remove the device from
            # bluez's DBus hierarchy.
            adapter.RemoveDevice(self._device.object_path)
        else:
            raise RuntimeError('Exceeded timeout waiting to disconnect from device!')

    def list_services(self):
        """Return a list of GattService objects that have been discovered for
        this device.
        """
        return map(BluezGattService, 
                   get_provider()._get_objects(_SERVICE_INTERFACE,
                                               self._device.object_path))

    def discover(self, service_uuids, char_uuids, timeout_sec=30):
        """Wait up to timeout_sec for the specified services and characteristics
        to be discovered on the device.  If the timeout is exceeded without
        discovering the services and characteristics then an exception is thrown.
        """
        # Turn expected values into a counter of each UUID for fast comparison.
        expected_services = Counter(service_uuids)
        expected_chars = Counter(char_uuids)
        # Loop trying to find the expected services for the device.
        start = time.time()
        while True:
            # Find actual services discovered for the device.
            actual_services = Counter(self.advertised)
            # Find actual characteristics discovered for the device.
            chars = map(BluezGattCharacteristic, 
                        get_provider()._get_objects(_CHARACTERISTIC_INTERFACE, 
                                                    self._device.object_path))
            actual_chars = Counter(map(lambda x: x.uuid, chars))
            # Compare actual discovered UUIDs with expected and return true if at
            # least the expected UUIDs are available.
            if actual_services >= expected_services and actual_chars >= expected_chars:
                # Found at least the expected services!
                return True
            # Couldn't find the devices so check if timeout has expired and try again.
            if time.time()-start >= timeout_sec:
                return False
            time.sleep(1)

    @property
    def advertised(self):
        """Return a list of UUIDs for services that are advertised by this
        device.
        """
        uuids = []
        # Get UUIDs property but wrap it in a try/except to catch if the property
        # doesn't exist as it is optional.
        try:
            uuids = self._props.Get(_INTERFACE, 'UUIDs')
        except dbus.exceptions.DBusException as ex:
            # Ignore error if device has no UUIDs property (i.e. might not be
            # a BLE device).
            if ex.get_dbus_name() != 'org.freedesktop.DBus.Error.InvalidArgs':
                raise ex
        return [uuid.UUID(str(x)) for x in uuids]

    @property
    def id(self):
        """Return a unique identifier for this device.  On supported platforms
        this will be the MAC address of the device, however on unsupported
        platforms (Mac OSX) it will be a unique ID like a UUID.
        """
        return self._props.Get(_INTERFACE, 'Address')

    @property
    def name(self):
        """Return the name of this device."""
        return self._props.Get(_INTERFACE, 'Name')

    @property
    def is_connected(self):
        """Return True if the device is connected to the system, otherwise False.
        """
        return self._props.Get(_INTERFACE, 'Connected')

    @property
    def rssi(self):
        """Return the RSSI signal strength in decibels."""
        return self._props.Get(_INTERFACE, 'RSSI')

    @property
    def _adapter(self):
        """Return the DBus path to the adapter that owns this device."""
        return self._props.Get(_INTERFACE, 'Adapter')
