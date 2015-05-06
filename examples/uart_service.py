# Example of interaction with a BLE UART device using a UART service
# implementation.
# Author: Tony DiCola
import Adafruit_BluetoothLE
from Adafruit_BluetoothLE.services import UART


# Get the BLE provider for the current platform.
ble = Adafruit_BluetoothLE.get_provider()


# Main function run in a background thread so that the main application thread 
# can run a GUI event loop (required for processing BLE events in the
# background).  You can return an int at any point and it will cause the program
# to exit with that status code.
def main():
    # Get the first available BLE network adapter and make sure it's powered on.
    adapter = ble.get_default_adapter()
    print 'Using adapter {0}...'.format(adapter.name)

    print 'Powering up adapter...'
    adapter.power_on()

    # Disconnect any currently connected UART devices.  Good for cleaning up and
    # starting from a fresh state.
    print 'Disconnecting any connected UART devices...'
    UART.disconnect_devices()

    # Scan for UART devices, either just by UART service type or by name (or
    # not shown but you can scan for both UART service type and name).
    print 'Searching for UART device...'
    try:
        adapter.start_scan()
        # Search for the first UART device found (by service type).
        device = UART.find_device(timeout_sec=30)
        if device is None:
            print ble._print_tree()
            raise RuntimeError('Failed to find UART device!')
    finally:
        # Make sure scanning is stopped before exiting.
        adapter.stop_scan()

    print 'Connecting to device...'
    device.connect(timeout_sec=30)

    # Once connected do everything else in a try/finally to make sure the device
    # is disconnected when done.
    try:
        # Wait for service discovery to complete for the UART service.
        print 'Discovering services...'
        UART.discover(device, timeout_sec=30)

        # Once service discovery is complete create an instance of the service
        # and start interacting with it.
        uart = UART(device)

        # Write a string to the TX characteristic.
        print 'Sending message to device...'
        uart.write('Hello world!\r\n')

        # Now sit in a loop printing out anything received from the device.
        print 'Waiting for data from device...'
        print 'Press Ctrl-C to quit.'
        while True:
            received = uart.read()
            print 'Received', received
    finally:
        # Make sure device is disconnected on exit.
        device.disconnect()


print 'Starting UART test...'
# Initialize the BLE system.  MUST be called before other BLE calls!
ble.initialize()
# Optionally clear any cached data because both bluez and CoreBluetooth have 
# issues with caching data and it going stale.  This is only necessary if you
# have devices changing their state like name, service, etc.
#ble.clear_cached_data()
# Start the mainloop to process BLE events, and run the provided function in
# a background thread.  When the provided main function stops runnings, returns
# an integer status code, or throws an error the program will exit.
ble.run_mainloop_with(main)
