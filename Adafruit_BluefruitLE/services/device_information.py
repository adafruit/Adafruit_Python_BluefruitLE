# Bluetooth LE device information service class.  Provides information about
# the connected BLE device.
# Author: Tony DiCola
#
# Copyright (c) 2015 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import uuid

from .servicebase import ServiceBase


# Define service and characteristic UUIDs.  These UUIDs are taken from the spec:
# https://developer.bluetooth.org/gatt/services/Pages/ServiceViewer.aspx?u=org.bluetooth.service.device_information.xml
DIS_SERVICE_UUID        = uuid.UUID('0000180A-0000-1000-8000-00805F9B34FB')
MANUFACTURER_CHAR_UUID  = uuid.UUID('00002A29-0000-1000-8000-00805F9B34FB')
MODEL_CHAR_UUID         = uuid.UUID('00002A24-0000-1000-8000-00805F9B34FB')
SERIAL_CHAR_UUID        = uuid.UUID('00002A25-0000-1000-8000-00805F9B34FB')
HW_REVISION_CHAR_UUID   = uuid.UUID('00002A27-0000-1000-8000-00805F9B34FB')
FW_REVISION_CHAR_UUID   = uuid.UUID('00002A26-0000-1000-8000-00805F9B34FB')
SW_REVISION_CHAR_UUID   = uuid.UUID('00002A28-0000-1000-8000-00805F9B34FB')
SYS_ID_CHAR_UUID        = uuid.UUID('00002A23-0000-1000-8000-00805F9B34FB')
REG_CERT_CHAR_UUID      = uuid.UUID('00002A2A-0000-1000-8000-00805F9B34FB')
PNP_ID_CHAR_UUID        = uuid.UUID('00002A50-0000-1000-8000-00805F9B34FB')


class DeviceInformation(ServiceBase):
    """Bluetooth LE device information service object."""

    # Configure expected services and characteristics for the DIS service.
    # Since characteristics are optional don't list any as explicit requirements.
    # Also most devices don't advertise the DIS service so don't list it as
    # required in advertisements.
    ADVERTISED = []
    SERVICES = [DIS_SERVICE_UUID]
    CHARACTERISTICS = []

    def __init__(self, device):
        """Initialize device information from provided bluez device."""
        # Find the DIS service and characteristics associated with the device.
        self._dis = device.find_service(DIS_SERVICE_UUID)
        self._manufacturer = self._dis.find_characteristic(MANUFACTURER_CHAR_UUID)
        self._model = self._dis.find_characteristic(MODEL_CHAR_UUID)
        self._serial = self._dis.find_characteristic(SERIAL_CHAR_UUID)
        self._hw_revision = self._dis.find_characteristic(HW_REVISION_CHAR_UUID)
        self._sw_revision = self._dis.find_characteristic(SW_REVISION_CHAR_UUID)
        self._fw_revision = self._dis.find_characteristic(FW_REVISION_CHAR_UUID)
        self._sys_id = self._dis.find_characteristic(SYS_ID_CHAR_UUID)
        self._reg_cert = self._dis.find_characteristic(REG_CERT_CHAR_UUID)
        self._pnp_id = self._dis.find_characteristic(PNP_ID_CHAR_UUID)

    # Expose all the DIS properties as easy to read python object properties.
    @property
    def manufacturer(self):
        if self._manufacturer is not None:
            return self._manufacturer.read_value()
        return None

    @property
    def model(self):
        if self._model is not None:
            return self._model.read_value()
        return None

    @property
    def serial(self):
        if self._serial is not None:
            return self._serial.read_value()
        return None

    @property
    def hw_revision(self):
        if self._hw_revision is not None:
            return self._hw_revision.read_value()
        return None

    @property
    def sw_revision(self):
        if self._sw_revision is not None:
            return self._sw_revision.read_value()
        return None

    @property
    def fw_revision(self):
        if self._fw_revision is not None:
            return self._fw_revision.read_value()
        return None

    @property
    def system_id(self):
        if self._sys_id is not None:
            return self._sys_id.read_value()
        return None

    @property
    def regulatory_cert(self):
        if self._reg_cert is not None:
            return self._reg_cert.read_value()
        return None

    @property
    def pnp_id(self):
        if self._pnp_id is not None:
            return self._pnp_id.read_value()
        return None
