from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(name              = 'Adafruit_BluetoothLE',
      version           = '1.0.0',
      author            = 'Tony DiCola',
      author_email      = 'tdicola@adafruit.com',
      description       = 'Python library for interacting with Bluetooth low energy devices on Linux or OSX.',
      license           = 'MIT',
      url               = 'https://github.com/adafruit/Adafruit_Python_BluetoothLE/',
      install_requires  = ['futures'],
      packages          = find_packages())
