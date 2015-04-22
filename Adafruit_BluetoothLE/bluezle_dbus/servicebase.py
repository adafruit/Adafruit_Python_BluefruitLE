# Bluetooth LE service base class.  Provides functions to simplify and decouple
# service implementations from specific BLE implementations.
# Author: Tony DiCola
import bluez
from gatt import GattService, GattCharacteristic


class ServiceBase(object):
    """Base class for Bluetooth LE service classes.  Derived classes should
    have two class-level attributes:
      - ADVERTISED: List of expected service UUIDs for advertised devices.
      - SERVICES: List of expected service UUIDs (includes advertised and
                  unadvertised services).
      - CHARACTERISTICS: List of expected characteristic UUIDs.
    """

    @classmethod
    def find_device(cls, **kwargs):
        """Find the first available device that supports this service and return
        it, or None if no device is found.  Will wait for up to timeout_sec
        seconds to find the device.
        """
        return bluez.find_device(cls.ADVERTISED, **kwargs)

    @classmethod
    def find_devices(cls):
        """Find all the available devices that support this service and
        returns a list of them.  Does not poll and will return immediately.
        """
        return bluez.find_devices(cls.ADVERTISED)

    @classmethod
    def discover_services(cls, device, timeout_sec=30):
        """Wait until the specified device has discovered the expected services
        and characteristics for this service.  Should be called once before other 
        calls are made on the service.  Returns true if the service has been
        discovered in the specified timeout, or false if not discovered.
        """
        return bluez.discover_services(device, cls.SERVICES, cls.CHARACTERISTICS,
                                       timeout_sec)
