# Base class for a BLE network adapter.  Each OS supported by the library should
# inherit from this class and implement the abstract methods.
# Author: Tony DiCola
import abc


class Adapter(object):
    """Base class for a BLE network adapter."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def name(self):
        """Return the name of this BLE network adapter."""
        raise NotImplementedError

    @abc.abstractmethod
    def start_scan(self, timeout_sec):
        """Start scanning for BLE devices with this adapter."""
        raise NotImplementedError

    @abc.abstractmethod
    def stop_scan(self, timeout_sec):
        """Stop scanning for BLE devices with this adapter."""
        raise NotImplementedError

    @abc.abstractproperty
    def is_scanning(self):
        """Return True if the BLE adapter is scanning for devices, otherwise
        return False.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def power_on(self):
        """Power on this BLE adapter."""
        raise NotImplementedError

    @abc.abstractmethod
    def power_off(self):
        """Power off this BLE adapter."""
        raise NotImplementedError

    @abc.abstractproperty
    def is_powered(self):
        """Return True if the BLE adapter is powered up, otherwise return False.
        """
        raise NotImplementedError
