# Example of interaction with a BLE UART device that has an RX and TX
# characteristic for receiving and sending data.
# Author: Tony DiCola
import logging
import time
import uuid

import Adafruit_BluetoothLE


# Enable debug output.
#logging.basicConfig(level=logging.DEBUG)

# Define service and characteristic UUIDs used by the UART service.
UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')

# Get the BLE provider for the current platform.
ble = Adafruit_BluetoothLE.platform.get_provider()


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
    ble.disconnect_devices([UART_SERVICE_UUID])
    #TODO: Disconnect won't work on bluez?

    # Scan for UART devices, either just by UART service type or by name (or
    # not shown but you can scan for both UART service type and name).
    print 'Searching for UART device...'
    try:
        adapter.start_scan()
        # Search for the device by the services it advertises (UART service):
        device = ble.find_device(service_uuids=[UART_SERVICE_UUID], timeout_sec=30)
        # OR search for the device by name:
        #device = ble.find_device(name='UART', timeout_sec=30)
        if device is None:
            raise RuntimeError('Failed to find UART device!')
    finally:
        # Make sure scanning is stopped before exiting.
        adapter.stop_scan()

    print 'Connecting to device...'
    device.connect(timeout_sec=30)

    # Once connected do everything else in a try/finally to make sure the device
    # is disconnected when done.
    try:
        # Wait for service discovery to complete for at least the specified
        # service and characteristic UUID lists.
        print 'Discovering services...'
        device.discover([UART_SERVICE_UUID], [TX_CHAR_UUID, RX_CHAR_UUID],
                        timeout_sec=30)

        # Find the UART service and its characteristics.
        uart = device.find_service(UART_SERVICE_UUID)
        rx = uart.find_characteristic(RX_CHAR_UUID)
        tx = uart.find_characteristic(TX_CHAR_UUID)

        # Write a string to the TX characteristic.
        print 'Sending message to device...'
        tx.write_value('Hello world!\r\n')

        # Function to receive RX characteristic changes.
        def received(data):
            print 'Received:', data

        # Turn on notification of RX characteristics using the callback above.
        print 'Subscribing to RX characteristic changes...'
        rx.start_notify(received)

        # Now just wait for 30 seconds to receive data.
        print 'Waiting 30 seconds to receive data...'
        time.sleep(30)
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
