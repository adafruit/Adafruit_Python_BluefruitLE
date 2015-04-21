# Smart Bulb Colorific! service class.  Provides control of a BLE RGB light bulb.
# Author: Tony DiCola
import uuid

from ..bluezle_dbus import ServiceBase


# Define service and characteristic UUIDs.
COLOR_SERVICE_UUID = uuid.UUID('00001802-0000-1000-8000-00805f9b34fb')
COLOR_CHAR_UUID    = uuid.UUID('00002a06-0000-1000-8000-00805f9b34fb')


class Colorific(ServiceBase):
    """Smart Bulb Colorific! service object."""

    # Configure expected services and characteristics.
    ADVERTISED = [COLOR_SERVICE_UUID]
    SERVICES = [COLOR_SERVICE_UUID]
    CHARACTERISTICS = [COLOR_CHAR_UUID]

    def __init__(self, device):
        """Initialize device information from provided bluez device."""
        # Get the color characteristic.
        self._colorific = device.find_service(COLOR_SERVICE_UUID)
        self._color = self._colorific.find_characteristic(COLOR_CHAR_UUID)

    def set_color(self, r, g, b):
        """Set the red, green, blue color of the bulb."""
        # See more details on the bulb's protocol from this guide:
        #   https://learn.adafruit.com/reverse-engineering-a-bluetooth-low-energy-light-bulb/overview
        command = '\x58\x01\x03\x01\xFF\x00' + chr(r & 0xFF) + chr(g & 0xFF) + chr(b & 0xFF)
        self._color.write_value(command)
