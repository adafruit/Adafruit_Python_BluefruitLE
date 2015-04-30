# Base class for a BLE device.  Each OS supported by the library should
# inherit from this class and implement the abstract methods.
# Author: Tony DiCola
import abc


class Device(object):
    """Base class for a BLE device."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def connect(self, timeout_sec):
        """Connect to the BLE device."""
        raise NotImplementedError

    @abc.abstractmethod
    def disconnect(self, timeout_sec):
        """Disconnect from the BLE device."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_services(self):
        """Return a list of GattService objects that have been discovered for
        this device.
        """
        raise NotImplementedError

    @abc.abstractproperty
    def discover(self, service_uuids, char_uuids, timeout_sec=30):
        """Wait up to timeout_sec for the specified services and characteristics
        to be discovered on the device.  If the timeout is exceeded without
        discovering the services and characteristics then an exception is thrown.
        """
        raise NotImplementedError

    @abc.abstractproperty
    def advertised(self):
        """Return a list of UUIDs for services that are advertised by this
        device.
        """
        raise NotImplementedError

    @abc.abstractproperty
    def id(self):
        """Return a unique identifier for this device.  On supported platforms
        this will be the MAC address of the device, however on unsupported
        platforms (Mac OSX) it will be a unique ID like a UUID.
        """
        raise NotImplementedError

    @abc.abstractproperty
    def name(self):
        """Return the name of this device."""
        raise NotImplementedError

    @abc.abstractproperty
    def is_connected(self):
        """Return True if the device is connected to the system, otherwise False.
        """
        raise NotImplementedError

    @abc.abstractproperty
    def rssi(self):
        """Return the RSSI signal strength in decibels."""
        raise NotImplementedError

    def find_service(self, uuid):
        """Return the first child service found that has the specified
        UUID.  Will return None if no service that matches is found.
        """
        for service in self.list_services():
            if service.uuid == uuid:
                return service
        return None
