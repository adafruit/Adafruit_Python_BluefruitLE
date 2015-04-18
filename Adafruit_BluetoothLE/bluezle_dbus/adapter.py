# Python object to represent the bluez DBus adapter object.  Provides properties
# and functions to easily interact with the DBus object.
# Author: Tony DiCola
import dbus

from bluezobject import BluezObject


class Adapter(BluezObject):
    """Bluetooth adapter object."""

    def __init__(self, dbus_obj):
        """Create an instance of the bluetooth adapter from the provided bluez
        DBus object.
        """
        super(Adapter, self).__init__(dbus_obj, 'org.bluez.Adapter1')
        self._adapter = dbus.Interface(self._object, 'org.bluez.Adapter1')

    def start_scan(self):
        self._adapter.StartDiscovery()

    def stop_scan(self):
        self._adapter.StopDiscovery()

    address = BluezObject.readonly_property('Address')

    name = BluezObject.readonly_property('Name')

    class_ = BluezObject.readonly_property('Class')

    alias = BluezObject.readwrite_property('Alias')

    powered = BluezObject.readwrite_property('Powered')

    discoverable = BluezObject.readwrite_property('Discoverable')

    pairable = BluezObject.readwrite_property('Pairable')

    pairable_timeout = BluezObject.readwrite_property('PairableTimeout')

    discoverable_timeout = BluezObject.readwrite_property('DiscoverableTimeout')

    discovering = BluezObject.readonly_property('Discovering')

    uuids = BluezObject.readonly_property('UUIDs', converter=BluezObject.to_uuids)

    modalias = BluezObject.readonly_property('Modalias')


# Prevent circular dependencies by importing bluez after classes that use it.
import bluez
