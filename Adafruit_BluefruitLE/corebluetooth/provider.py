# BLE provider implementation using Mac OSX's CoreBluetooth library.
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
from future.utils import raise_
import logging
import os
from past.builtins import map
import sys
import subprocess
import threading
import time

import objc
from PyObjCTools import AppHelper

from ..interfaces import Provider
from ..platform import get_provider

from .metadata import CoreBluetoothMetadata
from .objc_helpers import uuid_to_cbuuid


# Load CoreBluetooth bundle.
objc.loadBundle("CoreBluetooth", globals(),
    bundle_path=objc.pathForFramework(u'/System/Library/Frameworks/IOBluetooth.framework/Versions/A/Frameworks/CoreBluetooth.framework'))

logger = logging.getLogger(__name__)


# Convenience functions to allow other classes to read global metadata lists
# associated with each CoreBluetooth type.
def device_list():
    return get_provider()._devices


def service_list():
    return get_provider()._services


def characteristic_list():
    return get_provider()._characteristics


def descriptor_list():
    return get_provider()._descriptors


class CentralDelegate(object):
    """Internal class to handle asyncronous BLE events from the operating system.
    """
    # Note that this class will be used by multiple threads (the main loop
    # thread that will receive async BLE events, and the secondary thread
    # that will receive requests from user code) so access to internal state

    def centralManagerDidUpdateState_(self, manager):
        """Called when the BLE adapter is powered on and ready to scan/connect
        to devices.
        """
        logger.debug('centralManagerDidUpdateState called')
        # Notify adapter about changed central state.
        get_provider()._adapter._state_changed(manager.state())

    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, manager, peripheral, data, rssi):
        """Called when the BLE adapter found a device while scanning, or has
        new advertisement data for a device.
        """
        logger.debug('centralManager_didDiscoverPeripheral_advertisementData_RSSI called')
        # Log name of device found while scanning.
        #logger.debug('Saw device advertised with name: {0}'.format(peripheral.name()))
        # Make sure the device is added to the list of devices and then update
        # its advertisement state.
        device = device_list().get(peripheral)
        if device is None:
            device = device_list().add(peripheral, CoreBluetoothDevice(peripheral))
        device._update_advertised(data)

    def centralManager_didConnectPeripheral_(self, manager, peripheral):
        """Called when a device is connected."""
        logger.debug('centralManager_didConnectPeripheral called')
        # Setup peripheral delegate and kick off service discovery.  For now just
        # assume all services need to be discovered.
        peripheral.setDelegate_(self)
        peripheral.discoverServices_(None)
        # Fire connected event for device.
        device = device_list().get(peripheral)
        if device is not None:
            device._set_connected()

    def centralManager_didFailToConnectPeripheral_error_(self, manager, peripheral, error):
        # Error connecting to devie.  Ignored for now since connected event will
        # never fire and a timeout will elapse.
        logger.debug('centralManager_didFailToConnectPeripheral_error called')

    def centralManager_didDisconnectPeripheral_error_(self, manager, peripheral, error):
        """Called when a device is disconnected."""
        logger.debug('centralManager_didDisconnectPeripheral called')
        # Get the device and remove it from the device list, then fire its
        # disconnected event.
        device = device_list().get(peripheral)
        if device is not None:
            # Fire disconnected event and remove device from device list.
            device._set_disconnected()
            device_list().remove(peripheral)

    def peripheral_didDiscoverServices_(self, peripheral, services):
        """Called when services are discovered for a device."""
        logger.debug('peripheral_didDiscoverServices called')
        # Make sure the discovered services are added to the list of known
        # services, and kick off characteristic discovery for each one.
        # NOTE: For some reason the services parameter is never set to a good
        # value, instead you must query peripheral.services() to enumerate the
        # discovered services.
        for service in peripheral.services():
            if service_list().get(service) is None:
                service_list().add(service, CoreBluetoothGattService(service))
            # Kick off characteristic discovery for this service.  Just discover
            # all characteristics for now.
            peripheral.discoverCharacteristics_forService_(None, service)

    def peripheral_didDiscoverCharacteristicsForService_error_(self, peripheral, service, error):
        """Called when characteristics are discovered for a service."""
        logger.debug('peripheral_didDiscoverCharacteristicsForService_error called')
        # Stop if there was some kind of error.
        if error is not None:
            return
        # Make sure the discovered characteristics are added to the list of known
        # characteristics, and kick off descriptor discovery for each char.
        for char in service.characteristics():
            # Add to list of known characteristics.
            if characteristic_list().get(char) is None:
                characteristic_list().add(char, CoreBluetoothGattCharacteristic(char))
            # Start descriptor discovery.
            peripheral.discoverDescriptorsForCharacteristic_(char)
        # Notify the device about the discovered characteristics.
        device = device_list().get(peripheral)
        if device is not None:
            device._characteristics_discovered(service)

    def peripheral_didDiscoverDescriptorsForCharacteristic_error_(self, peripheral, characteristic, error):
        """Called when characteristics are discovered for a service."""
        logger.debug('peripheral_didDiscoverDescriptorsForCharacteristic_error called')
        # Stop if there was some kind of error.
        if error is not None:
            return
        # Make sure the discovered descriptors are added to the list of known
        # descriptors.
        for desc in characteristic.descriptors():
            # Add to list of known descriptors.
            if descriptor_list().get(desc) is None:
                descriptor_list().add(desc, CoreBluetoothGattDescriptor(desc))

    def peripheral_didWriteValueForCharacteristic_error_(self, peripheral, characteristic, error):
        # Characteristic write succeeded.  Ignored for now.
        logger.debug('peripheral_didWriteValueForCharacteristic_error called')

    def peripheral_didUpdateNotificationStateForCharacteristic_error_(self, peripheral, characteristic, error):
        # Characteristic notification state updated.  Ignored for now.
        logger.debug('peripheral_didUpdateNotificationStateForCharacteristic_error called')

    def peripheral_didUpdateValueForCharacteristic_error_(self, peripheral, characteristic, error):
        """Called when characteristic value was read or updated."""
        logger.debug('peripheral_didUpdateValueForCharacteristic_error called')
        # Stop if there was some kind of error.
        if error is not None:
            return
        # Notify the device about the updated characteristic value.
        device = device_list().get(peripheral)
        if device is not None:
            device._characteristic_changed(characteristic)

    def peripheral_didUpdateValueForDescriptor_error_(self, peripheral, descriptor, error):
        """Called when descriptor value was read or updated."""
        logger.debug('peripheral_didUpdateValueForDescriptor_error called')
        # Stop if there was some kind of error.
        if error is not None:
            return
        # Notify the device about the updated descriptor value.
        device = device_list().get(peripheral)
        if device is not None:
            device._descriptor_changed(descriptor)

    def peripheral_didReadRSSI_error_(self, peripheral, rssi, error):
        """Called when a new RSSI value for the peripheral is available."""
        logger.debug('peripheral_didReadRSSI_error called')
        # Note this appears to be completely undocumented at the time of this
        # writing.  Can see more details at:
        #  http://stackoverflow.com/questions/25952218/ios-8-corebluetooth-deprecated-rssi-methods
        # Stop if there was some kind of error.
        if error is not None:
            return
        # Notify the device about the updated RSSI value.
        device = device_list().get(peripheral)
        if device is not None:
            device._rssi_changed(rssi)


class CoreBluetoothProvider(Provider):
    """BLE provider implementation using the CoreBluetooth framework."""

    def __init__(self):
        # Global state for BLE devices and other metadata.
        self._central_delegate = CentralDelegate()
        self._central_manager = None
        self._user_thread = None
        self._adapter = CoreBluetoothAdapter()
        # Keep an internal cache of the devices, services, characteristics, and
        # descriptors that are known to the system.  Extra metadata can be stored
        # with each item, like callbacks and events to fire when asyncronous BLE
        # events occur.
        self._devices = CoreBluetoothMetadata()
        self._services = CoreBluetoothMetadata()
        self._characteristics = CoreBluetoothMetadata()
        self._descriptors = CoreBluetoothMetadata()

    def initialize(self):
        """Initialize the BLE provider.  Must be called once before any other
        calls are made to the provider.
        """
        # Setup the central manager and its delegate.
        self._central_manager = CBCentralManager.alloc()
        self._central_manager.initWithDelegate_queue_options_(self._central_delegate,
                                                              None, None)
        # Add any connected devices to list of known devices.


    def run_mainloop_with(self, target):
        """Start the OS's main loop to process asyncronous BLE events and then
        run the specified target function in a background thread.  Target
        function should be a function that takes no parameters and optionally
        return an integer response code.  When the target function stops
        executing or returns with value then the main loop will be stopped and
        the program will exit with the returned code.

        Note that an OS main loop is required to process asyncronous BLE events
        and this function is provided as a convenience for writing simple tools
        and scripts that don't need to be full-blown GUI applications.  If you
        are writing a GUI application that has a main loop (a GTK glib main loop
        on Linux, or a Cocoa main loop on OSX) then you don't need to call this
        function.
        """
        # Create background thread to run user code.
        self._user_thread = threading.Thread(target=self._user_thread_main,
                                             args=(target,))
        self._user_thread.daemon = True
        self._user_thread.start()
        # Run main loop.  This call will never return!
        try:
            AppHelper.runConsoleEventLoop(installInterrupt=True)
        except KeyboardInterrupt:
            AppHelper.stopEventLoop()
            sys.exit(0)

    def _user_thread_main(self, target):
        """Main entry point for the thread that will run user's code."""
        try:
            # Run user's code.
            return_code = target()
            # Assume good result (0 return code) if none is returned.
            if return_code is None:
                return_code = 0
            # Call exit on the main thread when user code has finished.
            AppHelper.callAfter(lambda: sys.exit(return_code))
        except Exception as ex:
            # Something went wrong.  Raise the exception on the main thread to exit.
            AppHelper.callAfter(self._raise_error, sys.exc_info())

    def _raise_error(self, exec_info):
        """Raise an exception from the provided exception info.  Used to cause
        the main thread to stop with an error.
        """
        # Rethrow exception with its original stack trace following advice from:
        # http://nedbatchelder.com/blog/200711/rethrowing_exceptions_in_python.html
        raise_(exec_info[1], None, exec_info[2])

    def list_adapters(self):
        """Return a list of BLE adapter objects connected to the system."""
        return [self._adapter]

    def list_devices(self):
        """Return a list of BLE devices known to the system."""
        return self._devices.list()

    def clear_cached_data(self):
        """Clear the internal bluetooth device cache.  This is useful if a device
        changes its state like name and it can't be detected with the new state
        anymore.  WARNING: This will delete some files underneath the running user's
        ~/Library/Preferences/ folder!

        See this Stackoverflow question for information on what the function does:
        http://stackoverflow.com/questions/20553957/how-can-i-clear-the-corebluetooth-cache-on-macos
        """
        # Turn off bluetooth.
        if self._adapter.is_powered:
            self._adapter.power_off()
        # Delete cache files and suppress any stdout/err output.
        with open(os.devnull, 'w') as devnull:
            subprocess.call('rm ~/Library/Preferences/com.apple.Bluetooth.plist',
                            shell=True, stdout=devnull, stderr=subprocess.STDOUT)
            subprocess.call('rm ~/Library/Preferences/ByHost/com.apple.Bluetooth.*.plist',
                            shell=True, stdout=devnull, stderr=subprocess.STDOUT)

    def disconnect_devices(self, service_uuids):
        """Disconnect any connected devices that have any of the specified
        service UUIDs.
        """
        # Get list of connected devices with specified services.
        cbuuids = map(uuid_to_cbuuid, service_uuids)
        for device in self._central_manager.retrieveConnectedPeripheralsWithServices_(cbuuids):
            self._central_manager.cancelPeripheralConnection_(device)


# Stop circular references by importing after classes that use these types.
from .adapter import CoreBluetoothAdapter
from .device import CoreBluetoothDevice
from .gatt import CoreBluetoothGattService, CoreBluetoothGattCharacteristic, CoreBluetoothGattDescriptor
