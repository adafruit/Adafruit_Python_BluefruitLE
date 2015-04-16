# Base class for bluezle-dbus objects.  Provides class methods to easily
# generate properties on bluez objects.
# Author: Tony DiCola
import dbus


class BluezObject(object):
    """Base class for bluezle-dbus objects."""

    def __init__(self, dbus_obj, interface):
        """Create instance of bluez object from provided DBus object and
        interface name.
        """
        # Save object and interface for property getters and setters to reference.
        self._object = dbus_obj
        self._interface = interface
        self._props = dbus.Interface(dbus_obj, 'org.freedesktop.DBus.Properties')

    @classmethod
    def _get_prop(cls, prop):
        # Generate a read function for the requested property.
        def _get(self):
            return self._props.Get(self._interface, prop)
        return _get

    @classmethod
    def _set_prop(cls, prop):
        # Generate a write function for the requested property.
        def _set(self, value):
            self._props.Set(self._interface, prop, value)
        return _set

    @classmethod
    def readonly_property(cls, prop):
        """Generate a read-only python object property for the specified bluez
        DBus object property.
        """
        return property(cls._get_prop(prop))

    @classmethod
    def readwrite_property(cls, prop):
        """Generate a writable python object property for the specified bluez
        DBus object property.
        """
        return property(cls._get_prop(prop), cls._set_prop(prop))
