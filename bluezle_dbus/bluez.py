# Functions to interact with bluez's DBus APIs.  These functions are module-level
# as opposed to being inside a class because there is only one global instance
# of bluez's DBus interface on the system and global module-level functions are a 
# natural way to interact with it.
# Author: Tony DiCola
import threading
import time
import uuid

import dbus
import dbus.mainloop.glib
from gi.repository import GObject

from adapter import Adapter
from device import Device


# Global DBus state, interface, and main loop thread.
_BUS = None
_BLUEZ = None
_MAINLOOP = None
_MAINLOOP_THREAD = None


def _mainloop_thread():
    # Spin up a GLib main loop.  Meant to be run as background thread.
    mainloop = GObject.MainLoop()
    mainloop.run()


def initialize():
    """Initialize bluez DBus communication.  Must be called before any other
    calls are made!.
    """
    global _BUS
    global _BLUEZ
    global _MAINLOOP
    global _MAINLOOP_THREAD
    # Ensure GLib's threading is initialized to support python threads, and make
    # a default mainloop that all DBus objects will inherit.  These commands MUST
    # execute before any other DBus commands!
    GObject.threads_init()
    dbus.mainloop.glib.threads_init()
    # Set the default main loop, this also MUST happen before other DBus calls.
    _MAINLOOP = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    # Get the main DBus system bus and root bluez object.
    _BUS = dbus.SystemBus()
    _BLUEZ = dbus.Interface(_BUS.get_object('org.bluez', '/'), 
                            'org.freedesktop.DBus.ObjectManager')
    # Spin up a background thread to run the GLib main loop that's required to
    # receive async DBus messages in the background.
    _MAINLOOP_THREAD = threading.Thread(target=_mainloop_thread)
    _MAINLOOP_THREAD.daemon = True
    _MAINLOOP_THREAD.start()


def get_objects(interface):
    """Return a list of all bluez DBus objects that implement the requested 
    interface name.
    """
    # Iterate through all the objects in bluez's DBus hierarchy and return any
    # that implement the requested interface.
    objects = []
    for path, interfaces in _BLUEZ.GetManagedObjects().iteritems():
        if interface in interfaces.keys():
            objects.append(_BUS.get_object('org.bluez', path))
    return objects


def find_devices(service_uuid):
    """Return devices that advertise the specified service UUID.  service_uuid
    should be a Python uuid.UUID object.
    """
    # Grab all the bluez devices.
    devices = map(Device, get_objects('org.bluez.Device1'))
    # Filter to just the devices that have the requested service UUID.  Since
    # the device service UUID parameter is optional, be careful to catch the
    # invalid argument error and ignore it.
    found = []
    for device in devices:
        try:
            for dev_uuid in device.uuids:
                if uuid.UUID(str(dev_uuid)) == service_uuid:
                    found.append(device)
        except dbus.exceptions.DBusException as ex:
            if ex.get_dbus_name() != 'org.freedesktop.DBus.Error.InvalidArgs':
                raise ex
    return found


def find_device(service_uuid, timeout_sec=0):
    """Return the first device found that advertises the specified service UUID.
    service_uuid should be a Python uuid.UUID object.  Will wait up to timeout_sec
    seconds for the device to be found, and if the timeout is zero then it will
    not wait at all and immediately return a result.  When no device is found
    a value of None is returned.
    """
    i = 0
    while True:
        # Call find_devices and grab the first result if any are found.
        found = find_devices(service_uuid)
        if len(found) > 0:
            return found[0]
        # If no device is found increase attempt count and check if exceeded
        # the timeout.
        i += 1
        if i >= timeout_sec:
            # Exceeded timeout, return no device.
            return None
        # Otherwise sleep for a second and try again.
        time.sleep(1)



def list_adapters():
    """Return a list of bluetooth adapter objects.
    """
    # Grab all the adapter objects and return them.
    return map(Adapter, get_objects('org.bluez.Adapter1'))


def get_default_adapter():
    """Return the first bluetooth adapter found, or None if no adapters are
    available.
    """
    adapters = list_adapters()
    if len(adapters) > 0:
        return adapters[0]
    else:
        return None


def _print_tree():
    """Print tree of all bluez objects, useful for debugging.
    """
    # This is based on the bluez sample code get-managed-objects.py.
    objects = _BLUEZ.GetManagedObjects()
    for path in objects.keys():
        print("[ %s ]" % (path))
        interfaces = objects[path]
        for interface in interfaces.keys():
            if interface in ["org.freedesktop.DBus.Introspectable",
                        "org.freedesktop.DBus.Properties"]:
                continue
            print("    %s" % (interface))
            properties = interfaces[interface]
            for key in properties.keys():
                print("      %s = %s" % (key, properties[key]))