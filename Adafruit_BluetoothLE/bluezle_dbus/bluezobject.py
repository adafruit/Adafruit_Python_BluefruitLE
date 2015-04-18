# Base class for bluezle-dbus objects.  Provides class methods to easily
# generate properties on bluez objects.
# Author: Tony DiCola
import uuid

import dbus


def _get_prop(prop, converter=None):
    # Generate a read function for the requested property.
    if converter is None:
        def _get(self):
            return self._props.Get(self._interface, prop)
    else:
        def _get(self):
            return converter(self._props.Get(self._interface, prop))
    return _get


def _set_prop(prop):
    # Generate a write function for the requested property.
    def _set(self, value):
        self._props.Set(self._interface, prop, value)
    return _set


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

    @staticmethod
    def readonly_property(prop, converter=None):
        """Generate a read-only python object property for the specified bluez
        DBus object property.
        """
        return property(_get_prop(prop, converter))

    @staticmethod
    def readwrite_property(prop):
        """Generate a writable python object property for the specified bluez
        DBus object property.
        """
        return property(_get_prop(prop), _set_prop(prop))

    @staticmethod
    def to_uuid(dbus_uuid):
        """Convert DBus UUID to python UUID."""
        return uuid.UUID(str(dbus_uuid))

    @staticmethod
    def to_uuids(dbus_uuids):
        """Convert DBus UUID list to python UUID list."""
        return [uuid.UUID(str(x)) for x in dbus_uuids]

    @property
    def object_path(self):
        return self._object.object_path
