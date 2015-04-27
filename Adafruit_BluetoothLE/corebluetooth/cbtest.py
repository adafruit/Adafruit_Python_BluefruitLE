import sys
import time
import uuid

import corebluetooth as cb


UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')


def main():
    print 'Powering up adapter...'
    cb.powered_on()

    print 'Disconnecting any connected UART devices...'
    for device in cb.list_connected_devices([UART_SERVICE_UUID]):
        device.disconnect()

    print 'Searching for UART device...'
    cb.start_scan()
    # Search for the device by the services it advertises (UART service):
    device = cb.find_device(serivce_uuids=[UART_SERVICE_UUID], timeout_sec=30)
    # OR search for the device by name:
    #device = cb.find_device(name='UART', timeout_sec=30)
    cb.stop_scan()
    if device is None:
        raise RuntimeError('Failed to find UART device!')

    print 'Connecting to device...'
    device.connect(timeout_sec=30)

    try:
        print 'Discovering services...'
        device.discover_services(timeout_sec=30)

        # Find the UART service and its characteristics.
        uart = device.find_service(UART_SERVICE_UUID)
        rx   = uart.find_characteristic(RX_CHAR_UUID)
        tx   = uart.find_characteristic(TX_CHAR_UUID)

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
cb.initialize()
cb.run_mainloop_with(main)
