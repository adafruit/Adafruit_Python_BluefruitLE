# Adafruit Python BluetoothLE

Python library to simplify access to Bluetooth low energy devices and services on Linux (using bluez) and Mac OSX (using CoreBluetooth).

This library provides a Python wrapper for BLE **Central Mode**, meaning it can initiate connections and data exchanges with other BLE Peripherals.  It does not allow you to emulate a BLE Peripheral via Python, or provide Python-based access to BLE peripherals connected to your system.

## Bluez Installation (Linux)

On Linux (like with a Raspberry Pi) you'll need to compile and install the latest version of Bluez, version 5.30,
to gain access to the Bluetooth LE API it exposes.  **Warning:** Be careful about installing a later version of Bluez on top of an existing install if you use a Linux desktop OS like Ubuntu, Debian, etc.  You might cause an issue with your Bluez installation which could break other parts of the OS that depend on it!  A better option is to move to a later version of the OS that has a properly packaged Bluez 5.30 installation package.

To install bluez open a command terminal and run the following
commands:
```
sudo apt-get update
sudo apt-get install libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev
wget www.kernel.org/pub/linux/bluetooth/bluez-5.30.tar.gz
tar xvfz bluez-5.30.tar.gz
cd bluez-5.30
./configure --disable-systemd
make
sudo make install
sudo cp ./src/bluetoothd /usr/local/bin/
```

Finally you'll want to make sure the bluetoothd daemon runs at boot, and is run with the `--experimental` flag to enable all the BLE APIs.  To do this edit the `/etc/rc.local` file and add the following line before the `exit 0` at the end:
```
/usr/local/bin/bluetoothd --experimental &
```

Save the changed file and reboot the pi.  Then verify using the command `ps aux | grep bluetoothd` that the bluetoothd daemon is running.
