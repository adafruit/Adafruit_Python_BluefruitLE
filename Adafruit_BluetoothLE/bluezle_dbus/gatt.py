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

    @property
    def characteristics(self):
        """Return list of GATT characteristics that have been discovered for this
        service.
        """
        return map(GattCharacteristic, bluez.get_objects_by_path(self._characteristics))

    def find_characteristic(self, uuid):
        """Return the first child characteristic found that has the specified
        UUID.  Will return None if no characteristic that matches is found.
        """
        for char in self.characteristics:
            if char.uuid == uuid:
                return char
        return None

    uuid = BluezObject.readonly_property('UUID', converter=BluezObject.to_uuid)

    primary = BluezObject.readonly_property('Primary')

    device = BluezObject.readonly_property('Device')

    _characteristics = BluezObject.readonly_property('Characteristics')


class GattCharacteristic(BluezObject):
    """Bluetooth LE GATT service characteristic object."""

    def __init__(self, dbus_obj):
        """Create an instance of the GATT characteristic from the provided bluez
        DBus object.
        """
        super(GattCharacteristic, self).__init__(dbus_obj, 'org.bluez.GattCharacteristic1')
        self._characteristic = dbus.Interface(dbus_obj, 'org.bluez.GattCharacteristic1')

    def read_value(self):
        """Read the value of this characteristic."""
        return self._characteristic.ReadValue()

    def write_value(self, value):
        """Write the specified value to this characteristic."""
        self._characteristic.WriteValue(value)

    def start_notify(self, on_change):
        """Enable notification of changes for this characteristic on the
        specified on_change callback.
        """
        # Setup a closure to be the first step in handling the on change callback.
        # This closure will verify the characteristic is changed and pull out the
        # new value to pass to the user's on change callback.
        def characteristic_changed(iface, changed_props, invalidated_props):
            # Check that this change is for a GATT characteristic and it has a
            # new value.
            if iface != 'org.bluez.GattCharacteristic1':
                return
            if 'Value' not in changed_props:
                return
            # Send the new value to the on_change callback.
            on_change(changed_props['Value'])
        # Hook up the property changed signal to call the closure above.
        self._props.connect_to_signal('PropertiesChanged', characteristic_changed)
        # Enable notifications for changes on the characteristic.
        self._characteristic.StartNotify()

    def stop_notify(self):
        self._characteristic.StopNotify()

    @property
    def descriptors(self):
        """Return list of GATT descriptors that have been discovered for this
        characteristic.
        """
        return map(GattDescriptor, bluez.get_objects_by_path(self._descriptors))

    def find_descriptor(self, uuid):
        """Return the first child descriptor found that has the specified
        UUID.  Will return None if no descriptor that matches is found.
        """
        for desc in self.descriptors:
            if desc.uuid == uuid:
                return desc
        return None

    uuid = BluezObject.readonly_property('UUID', converter=BluezObject.to_uuid)

    service = BluezObject.readonly_property('Service')

    value = BluezObject.readonly_property('Value')

    notifying = BluezObject.readonly_property('Notifying')

    flags = BluezObject.readonly_property('Flags')

    _descriptors = BluezObject.readonly_property('Descriptors')


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

    uuid = BluezObject.readonly_property('UUID', converter=BluezObject.to_uuid)

    characteristic = BluezObject.readonly_property('Characteristic')

    value = BluezObject.readonly_property('Value')


# Prevent circular dependencies by importing bluez after clases that use it.
import bluez
