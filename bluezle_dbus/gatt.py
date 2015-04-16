# Python objects to represent the bluez DBus GATT objects.  Provides properties
# and functions to easily interact with the DBus objects.
# Author: Tony DiCola
import dbus

from bluezobject import BluezObject


class GattService(BluezObject):
    """Bluetooth LE GATT service object."""

    def __init__(self, dbus_obj):
        """Create an instance of the GATT service from the provided bluez
        DBus object.
        """
        super(GattService, self).__init__(dbus_obj, 'org.bluez.GattService1')

    uuid = BluezObject.readonly_property('UUID')

    primary = BluezObject.readonly_property('Primary')

    device = BluezObject.readonly_property('Device')

    characteristics = BluezObject.readonly_property('Characteristics')


class GattCharacteristic(BluezObject):
    """Bluetooth LE GATT service characteristic object."""

    def __init__(self, dbus_obj):
        """Create an instance of the GATT characteristic from the provided bluez
        DBus object.
        """
        super(GattCharacteristic, self).__init__(dbus_obj, 'org.bluez.GattCharacteristic1')
        self._characteristic = dbus.Interface(dbus_obj, 'org.bluez.GattCharacteristic1')

    def read_value(self):
        return self._characteristic.ReadValue()

    def write_value(self, value):
        self._characteristic.WriteValue(value)

    def start_notify(self):
        self._characteristic.StartNotify()

    def stop_notify(self):
        self._characteristic.StopNotify()

    uuid = BluezObject.readonly_property('UUID')

    service = BluezObject.readonly_property('Service')

    value = BluezObject.readonly_property('Value')

    notifying = BluezObject.readonly_property('Notifying')

    flags = BluezObject.readonly_property('Flags')

    descriptors = BluezObject.readonly_property('Descriptors')


class GattDescriptor(BluezObject):
    """Bluetooth LE GATT characteristic descriptor object."""

    def __init__(self, dbus_obj):
        """Create an instance of the GATT descriptor from the provided bluez
        DBus object.
        """
        super(GattDescriptor, self).__init__(dbus_obj, 'org.bluez.GattDescriptor1')
        self._descriptor = dbus.Interface(dbus_obj, 'org.bluez.GattDescriptor1')

    def read_value(self):
        return self._descriptor.ReadValue()

    def write_value(self, value):
        self._descriptor.WriteValue(value)

    uuid = BluezObject.readonly_property('UUID')

    characteristic = BluezObject.readonly_property('Characteristic')

    value = BluezObject.readonly_property('Value')


# Prevent circular dependencies by importing bluez after clases that use it.
import bluez
