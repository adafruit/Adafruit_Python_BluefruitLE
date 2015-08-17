# Bluetooth LE device information service class.  Provides information about
# the connected BLE device.
# Author: Tony DiCola
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
        return self._manufacturer.read_value()

    @property
    def model(self):
        return self._model.read_value()

    @property
    def serial(self):
        return self._serial.read_value()

    @property
    def hw_revision(self):
        return self._hw_revision.read_value()

    @property
    def sw_revision(self):
        return self._sw_revision.read_value()

    @property
    def fw_revision(self):
        return self._fw_revision.read_value()

    @property
    def system_id(self):
        return self._sys_id.read_value()

    @property
    def regulatory_cert(self):
        return self._reg_cert.read_value()

    @property
    def pnp_id(self):
        return self._pnp_id.read_value()
