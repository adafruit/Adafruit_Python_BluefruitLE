import sys
import time
import uuid

import corebluetooth as cb


UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')

# Main function will run after the cb.run_mainloop_with function is called with
# it.  The main will run in a background thread so that the main application
# thread can run a GUI event loop (required for processing BLE events in the
# background).  You can return an int at any point and it will cause the program
# to exit with that status code.
def main():
    # Make sure internal BLE radio for machine is turned on and ready.  There is
    # an optional timeout in seconds (default is 30 seconds).
    print 'Powering up adapter...'
    cb.powered_on()

    # Disconnect any currently connected UART devices.  Good for cleaning up and
    # starting from a fresh state.
    print 'Disconnecting any connected UART devices...'
    for device in cb.list_connected_devices([UART_SERVICE_UUID]):
        device.disconnect()

    # Scan for UART devices, either just by UART service type or by name (or
    # not shown but you can scan for both UART service type and name).
    print 'Searching for UART device...'
    cb.start_scan()
    # Search for the device by the services it advertises (UART service):
    device = cb.find_device(service_uuids=[UART_SERVICE_UUID], timeout_sec=30)
    # OR search for the device by name:
    #device = cb.find_device(name='UART', timeout_sec=30)
    cb.stop_scan()
    if device is None:
        raise RuntimeError('Failed to find UART device!')

    print 'Connecting to device...'
    device.connect(timeout_sec=30)

    # Once connected do everything else in a try/finally to make sure the device
    # is disconnected when done.
    try:
        print 'Discovering services...'
        device.discover_services(timeout_sec=30)

        # Wait a few seconds to finish descriptor discovery for now.
        time.sleep(2)

        # Find the UART service and its characteristics.
        uart = device.find_service(UART_SERVICE_UUID)
        if uart is None:
            raise RuntimeError('Failed to find the expected UART service.  Is the right device connected?')
        rx = uart.find_characteristic(RX_CHAR_UUID)
        if rx is None:
            raise RuntimeError('Failed to find the expected RX characteristic.  Is the right device connected?')
        tx = uart.find_characteristic(TX_CHAR_UUID)
        if tx is None:
            raise RuntimeError('Failed to find the expected TX characteristic.  Is the right device connected?')

        # Write a string to the TX characteristic.
        tx.write_value('Hello world!\r\n')

        # Function to receive RX characteristic changes.
        def received(data):
            print 'Received:', data

        # Turn on notification of RX characteristics using the callback above.
        rx.start_notify(received)

        # Now just wait for 30 seconds to receive data.
        print 'Waiting 30 seconds to receive data...'
        time.sleep(30)
    finally:
        # Make sure device is disconnected on exit.
        device.disconnect()


# Program flow start here.  Initialize corebluetooth and then start its main
# event loop and run the main function above in a background thread.  When the
# main function stops runnings the program will exit.
print 'Start'
# First clear the bluetooth cache to prevent issues with devices that changed
# their name, services, etc.
cb.clear_bluetooth_cache()
# Now initialize bluetooth and run the main loop.
cb.initialize()
cb.run_mainloop_with(main)
