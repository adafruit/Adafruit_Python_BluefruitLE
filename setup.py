from setuptools import setup, find_packages
import platform

platform_install_requires = []

if platform.system() == 'Darwin':
    platform_install_requires += ['pyobjc-framework-CoreBluetooth']

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name              = 'Adafruit_BluefruitLE',
      version           = '0.9.10',
      author            = 'Tony DiCola',
      author_email      = 'tdicola@adafruit.com',
      description       = 'Python library for interacting with Bluefruit LE (Bluetooth low energy) devices on Linux or OSX.',
      long_description  = long_description,
      license           = 'MIT',
      url               = 'https://github.com/adafruit/Adafruit_Python_BluefruitLE/',
      install_requires  = ['future'] + platform_install_requires,
      packages          = find_packages())
