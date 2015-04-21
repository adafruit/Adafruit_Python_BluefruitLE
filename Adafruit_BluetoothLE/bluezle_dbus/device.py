# Python object to represent the bluez DBus device object.  Provides properties
# and functions to easily interact with the DBus object.
# Author: Tony DiCola
import dbus

from adapter import Adapter
import bluez
from bluezobject import BluezObject
from gatt import GattService


class Device(BluezObject):
    """Bluetooth device object."""

    def __init__(self, dbus_obj):
        """Create an instance of the bluetooth device from the provided bluez
        DBus object.
        """
        super(Device, self).__init__(dbus_obj, 'org.bluez.Device1')
        self._device = dbus.Interface(dbus_obj, 'org.bluez.Device1')

    def connect(self):
        self._device.Connect()

    def disconnect(self):
        self._device.Disconnect()

    def remove(self):
        # Remove device from any connected adapter and remove/unpair it.
        # Must be done at the adapter level so get the adapter for this device
        # and then remove the device.
        adapter = Adapter(bluez._BUS.get_object('org.bluez', self.adapter))
        adapter._adapter.RemoveDevice(self._device.object_path)

    @property
    def services(self):
        """Return a list of GattService objects that have been discovered for
        this device.
        """
        return map(GattService, bluez.get_objects('org.bluez.GattService1',
                                                  self._device.object_path))

    def find_service(self, uuid):
        """Return the first child service found that has the specified
        UUID.  Will return None if no service that matches is found.
        """
        for service in self.services:
            if service.uuid == uuid:
                return service
        return None

    address = BluezObject.readonly_property('Address')

    name = BluezObject.readonly_property('Name')

    icon = BluezObject.readonly_property('Icon')

    class_ = BluezObject.readonly_property('Class')

    appearance = BluezObject.readonly_property('Appearance')

    uuids = BluezObject.readonly_property('UUIDs', converter=BluezObject.to_uuids)

    paired = BluezObject.readonly_property('Paired')

    connected = BluezObject.readonly_property('Connected')

    trusted = BluezObject.readwrite_property('Trusted')

    blocked = BluezObject.readwrite_property('Blocked')

    alias = BluezObject.readwrite_property('Alias')

    adapter = BluezObject.readonly_property('Adapter')

    legacy_pairing = BluezObject.readonly_property('LegacyPairing')

    modalias = BluezObject.readonly_property('Modalias')

    rssi = BluezObject.readonly_property('RSSI')


# Prevent circular dependencies by importing bluez after classes that use it.
import bluez
