from collections import Counter
import Queue
import signal
import sys
import time
import threading
import uuid

import objc
from PyObjCTools import AppHelper


objc.loadBundle("CoreBluetooth", globals(),
            bundle_path=objc.pathForFramework(u'/System/Library/Frameworks/IOBluetooth.framework/Versions/A/Frameworks/CoreBluetooth.framework'))


# Global state for BLE devices and other metadata.
_CENTRAL_DELEGATE = None           # Global delegate that receives async BLE events.
_CENTRAL_MANAGER = None            # Global BLE central interface.
_USER_THREAD = None                # Thread running user code in the background.
_DEVICES = {}                      # Master dict of known devices.
_DEVICES_LOCK = threading.Lock()   # Lock to synchronize access to master device list across threads.
_POWERED_ON = threading.Event()    # Event to notify when adapter is powered on.


def cbuuid_to_uuid(cbuuid):
    """Convert Objective-C CBUUID type to native Python UUID type."""
    data = cbuuid.data().bytes()
    if len(data) == 2:
        # Short 16-bit UUID
        return uuid.UUID(bytes='\x00\x00{0}{1}\x00\x00\x10\x00\x80\x00\x00\x80\x5F\x9B\x34\xFB'.format(data[0], data[1]))
    elif len(data) == 4:
        # Short 32-bit UUID
        return uuid.UUID(bytes='{0}{1}{2}{3}\x00\x00\x10\x00\x80\x00\x00\x80\x5F\x9B\x34\xFB'.format(data[0], data[1], data[2], data[3]))
    else:
        # Full 128-bit UUID
        return uuid.UUID(bytes=data)


def uuid_to_cbuuid(uuid):
    """Convert native Python UUID type to Objective-C CBUUID type."""
    return CBUUID.UUIDWithString_(str(uuid))


def nsuuid_to_uuid(nsuuid):
    """Convert Objective-C NSUUID type to native Python UUID type."""
    return uuid.UUID(nsuuid.UUIDString())


def _get_device(peripheral):
    # Return any known devie instance for the specified peripheral.
    with _DEVICES_LOCK:
        device_uuid = nsuuid_to_uuid(peripheral.identifier())
        return _DEVICES.get(device_uuid, None)

def _sigint_handler(signum, frame):
    # SIGINT handler to quit program from Ctrl-C.  Tell the main loop to stop
    # and exit the program.
    AppHelper.callAfter(lambda: sys.exit(0))


class GattCharacteristic(object):
    """BLE device GATT characteristic representation."""
    
    def __init__(self, characteristic, peripheral):
        self._characteristic = characteristic  # Objective-C CBCharacteristic instance.
        self._peripheral = peripheral          # Objective-C CBPeripheral that owns this
                                               # characteristic instance.

    def write_value(self, value, write_type=0):
        """Set the value of the characteristic to the specified string."""
        # Convert data to NSData array of bytes, then write to the characteristic.
        data = NSData.dataWithBytes_length_(value, len(value))
        self._peripheral.writeValue_forCharacteristic_type_(data, 
                                                            self._characteristic, 
                                                            write_type)

    def start_notify(self, on_changed):
        """Call the specified callback whenever this characteristic is changed.
        """
        device = _get_device(self._peripheral)
        if device is None:
            return
        # Tell the device what callback to use for changes to this characteristic.
        device._characteristic_notify(self._characteristic, on_changed)
        # Turn on notifications of characteristic changes.
        self._peripheral.setNotifyValue_forCharacteristic_(True,
                                                           self._characteristic)

    def stop_notify(self):
        """Stop notifications for changes to this characteristic."""
        self._peripheral.setNotifyValue_forCharacteristic_(False,
                                                           self._characteristic)


class GattService(object):
    """BLE device GATT service representation."""
    
    def __init__(self, service):
        self._service = service  # Objective-C CBService instance for this service.

    def find_characteristic(self, uuid):
        """Return the GattCharacteristic instance with the specified UUID.  Will
        return the first instance found.  Will return the first instance found or
        None if no service is found.
        """
        for char in self._service.characteristics():
            if cbuuid_to_uuid(char.UUID()) == uuid:
                return GattCharacteristic(char, self._service.peripheral())
        return None


class Device(object):
    """BLE device representation."""

    def __init__(self, peripheral):
        self._peripheral = peripheral          # Objective-C CBPeripheral instance.
        self._name = None                      # Device name, found from advertisement.
        self._uuids = []                       # List of service UUIDs for this device.
        self._connected = threading.Event()    # Event to signal device connected.
        self._discovered = threading.Event()   # Event to signal service discovery complete.
        self._discovered_services = Counter()  # Count of in progress discovered services.
        self._char_notify = {}                 # Mapping of on_change handlers to call for
                                               # each charactersitic.

    def _update_advertised(self, advertised):
        # Advertisement data was received, pull out advertised service UUIDs and
        # name from advertisement data.
        if 'kCBAdvDataServiceUUIDs' in advertised:
            self._uuids = map(cbuuid_to_uuid, advertised['kCBAdvDataServiceUUIDs'])
        elif 'kCBAdvDataLocalName' in advertised:
            self._name = advertised['kCBAdvDataLocalName']

    def _services_discovered(self, services):
        # List of services was discovered, save it and kick off discovery of 
        # each service's characteristics.
        self._uuids = map(lambda x: cbuuid_to_uuid(x.UUID()), services)
        for service in services:
            self._peripheral.discoverCharacteristics_forService_(None, service)

    def _characteristics_discovered(self, service):
        # Characteristics for the specified service were discovered.  Update
        # counter of discovered services and signal when all have been discovered.
        service_uuid = cbuuid_to_uuid(service.UUID())
        self._discovered_services[service_uuid] += 1
        if self._discovered_services >= Counter(self._uuids):
            # Found all the services characteristics, finally time to fire the
            # service discovery complete event.
            self._discovered.set()

    def _characteristic_notify(self, characteristic, on_changed):
        # Associate the specified on_changed callback with any changes to this
        # characteristic.
        self._char_notify[cbuuid_to_uuid(characteristic.UUID())] = on_changed

    def _characteristic_changed(self, characteristic): #, value):
        # Called when a characteristic is changed.  Get the on_changed handler
        # for this characteristic (if it exists) and call it.
        on_changed = self._char_notify.get(cbuuid_to_uuid(characteristic.UUID()), None)
        if on_changed is not None:
            on_changed(characteristic.value().bytes().tobytes())

    def connect(self, timeout_sec=30):
        """Connect to the device, waiting up to the specified timeout.  If the
        timeout is exceeded and exception is thrown.
        """
        _CENTRAL_MANAGER.connectPeripheral_options_(self._peripheral, None)
        if not self._connected.wait(timeout_sec):
            raise RuntimeError('Failed to connect to device within timeout period!')

    def disconnect(self):
        """Disconnect from the device.  Note this will not wait for the disconnect
        to finish and it will happen in the background.
        """
        _CENTRAL_MANAGER.cancelPeripheralConnection_(self._peripheral)

    def discover_services(self, timeout_sec=30):
        """Wait for service discovery to complete for this device and return
        when ready.  Will wait up to timeout seconds for service discovery and
        throw and exception if discovery is not complete within the timeout.
        """
        if not self._discovered.wait(timeout_sec):
            raise RuntimeError('Failed to discover device services within timeout period!')

    def find_service(self, uuid):
        """Return the GattService instance with the specified UUID.  Will return
        the first instance found or None if no service is found.
        """
        for service in self._peripheral.services():
            if cbuuid_to_uuid(service.UUID()) == uuid:
                return GattService(service)
        return None

    @property
    def uuids(self):
        """List of service UUIDs associated with this device.  Until service
        discovery completes this will just be the list of advertised services.
        """
        return self._uuids

    @property
    def name(self):
        """Name of the device."""
        return self._name

    @property
    def connected(self):
        """Boolean that indicates if this device is connected to the adapter."""
        return self._connected.is_set()

 
class _BLEDelegate(object):
    # Internal class to handle asyncronous BLE events from the operating system.

    def __init__(self):
        pass
 
    def centralManagerDidUpdateState_(self, manager):
        # BLE adapter is powered on and ready for scanning.
        _POWERED_ON.set()
 
    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, manager, peripheral, data, rssi):
        # Device was found while scanning, or updated advertising data was
        # discovered.  Make sure the device is added to the global list of
        # devices and then update its advertisement state.
        with _DEVICES_LOCK:
            device_uuid = nsuuid_to_uuid(peripheral.identifier())
            if device_uuid not in _DEVICES:
                _DEVICES[device_uuid] = Device(peripheral)
            # Tell the device to update its state based on the advertised data.
            _DEVICES[device_uuid]._update_advertised(data)
 
    def centralManager_didConnectPeripheral_(self, manager, peripheral):
        # Device was connected.  Signal connection complete and kick off the
        # service discovery.
        device = _get_device(peripheral)
        if device is None:
            return
        # Setup peripheral delegate and kick off service discovery.
        peripheral.setDelegate_(self)
        peripheral.discoverServices_(None)
        # Fire connected event for device.
        device._connected.set()
 
    def centralManager_didFailToConnectPeripheral_error_(self, manager, peripheral, error):
        # Error connecting to devie.  Ignored for now since connected event will
        # never fire and a timeout will elapse.
        pass
 
    def centralManager_didDisconnectPeripheral_error_(self, manager, peripheral, error):
        # Device disconnected for some reason.  Remove device from global device
        # dict.
        with _DEVICES_LOCK:
            device_uuid = nsuuid_to_uuid(peripheral.identifier())
            if device_uuid in _DEVICES:
                del _DEVICES[device_uuid]

    def peripheral_didDiscoverServices_(self, peripheral, services):
        # Services were discovered for a device.  Notify the device about the
        # discovered services.
        device = _get_device(peripheral)
        if device is None:
            return
        device._services_discovered(peripheral.services())
 
    def peripheral_didDiscoverCharacteristicsForService_error_(self, peripheral, service, error):
        # Characteristics were discovered for a service.  Notify the device that
        # the service discovery is complete for that service.
        if error is not None:
            return
        device = _get_device(peripheral)
        if device is None:
            return
        device._characteristics_discovered(service)
 
    def peripheral_didWriteValueForCharacteristic_error_(self, peripheral, characteristic, error):
        # Characteristic write succeeded.  Ignored for now.
        pass
 
    def peripheral_didUpdateNotificationStateForCharacteristic_error_(self, peripheral, characteristic, error):
        # Characteristic notification state updated.  Ignored for now.
        pass
 
    def peripheral_didUpdateValueForCharacteristic_error_(self, peripheral, characteristic, error):
        # Characteristic value was updated.  Tell the device about the new
        # characteristic value.
        if error is not None:
            return
        device = _get_device(peripheral)
        if device is None:
            return
        device._characteristic_changed(characteristic)#, characteristic.value().bytes().tobytes())


def initialize():
    """Initialize the BLE library.  Must be called before any other functions!
    """
    global _CENTRAL_DELEGATE
    global _CENTRAL_MANAGER
    # Setup the central manager and its delegate.
    _CENTRAL_DELEGATE = _BLEDelegate()
    _CENTRAL_MANAGER = CBCentralManager.alloc()
    _CENTRAL_MANAGER.initWithDelegate_queue_options_(_CENTRAL_DELEGATE, None, None)


def _user_thread_main(target):
    # Main entry point for the thread that will run user's code.
    try:
        # Run user's code.
        return_code = target()
        # Call exit on the main thread when user code has finished.
        if return_code is None:
            return_code = 0
        AppHelper.callAfter(lambda: sys.exit(return_code))
    except Exception as ex:
        # Something went wrong.  Fail with an error and raise the exception.
        AppHelper.callAfter(lambda: sys.exit(-1))
        raise ex


def run_mainloop_with(target):
    """Start the application's main loop to process asyncronous BLE events, and
    spawn a background thread to run the desired target function.
    """
    # Create background thread to run user code.
    _USER_THREAD = threading.Thread(target=_user_thread_main, args=(target,))
    _USER_THREAD.daemon = True
    _USER_THREAD.start()
    # Run main loop.  This call will never return!
    AppHelper.runConsoleEventLoop()


def powered_on(timeout_sec=30):
    """Wait until the machine's BLE adapter is powered on and then return.  If
    the BLE adapter is not powered on within the specified timeout then an
    exception is thrown.
    """
    if not _POWERED_ON.wait(timeout_sec):
        raise RuntimeError('Timeout exceeded waiting for adapter to power on!')


def list_devices():
    """Return a list of all discovered devices.
    """
    with _DEVICES_LOCK:
        return _DEVICES.values()


def list_connected_devices(service_uuids):
    """Return list of all devices currently connected that have the specified
    service UUIDs.
    """
    # Convert list of service UUIDs to CBUUID types.
    cbuuids = map(uuid_to_cbuuid, service_uuids)
    # Return list of connected devices with specified services.
    return map(Device, _CENTRAL_MANAGER.retrieveConnectedPeripheralsWithServices_(cbuuids))


def find_devices(service_uuids=[], name=None):
    """Return devices that advertise the specified service UUIDs and/or have the
    specified name.  Service_uuids should be a list of Python uuid.UUID object
    and is optional.  Name is a string device name to look for and is also
    optional. 
    """
    # Convert service UUID list to counter for quicker comparison.
    expected = Counter(service_uuids)
    # Grab all the devices.
    devices = list_devices()
    # Filter to just the devices that have the requested service UUID/name.
    found = []
    for device in devices:
        if name is not None and device.name == name:
            # Check if the name matches and add the device.
            found.append(device)
        else:
            # Check if the advertised UUIDs have at least the expected UUIDs.
            actual = Counter(device.uuids)
            if actual >= expected:
                found.append(device)
    return found


def find_device(service_uuids=[], name=None, timeout_sec=30):
    """Return the first device that advertises the specified service UUIDs or
    has the specified name. Will wait up to timeout_sec seconds for the device 
    to be found, and if the timeout is zero then it will not wait at all and 
    immediately return a result.  When no device  is found a value of None is 
    returned.
    """
    start = time.time()
    while True:
        # Call find_devices and grab the first result if any are found.
        found = find_devices(service_uuids, name)
        if len(found) > 0:
            return found[0]
        # No device was found.  Check if the timeout is exceeded and wait to try
        # again.
        if time.time()-start >= timeout_sec:
            # Failed to find a device within the timeout.
            return None
        time.sleep(1)


def start_scan():
    """Start scanning for BLE devices."""
    _CENTRAL_MANAGER.scanForPeripheralsWithServices_options_(None, None)


def stop_scan():
    """Stop scanning for BLE devices."""
    _CENTRAL_MANAGER.stopScan()
