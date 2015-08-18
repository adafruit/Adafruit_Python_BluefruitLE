# Objective-C helper functions to convert between Python and Objective-C types.
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
import uuid

import objc


# Load CoreBluetooth bundle.
objc.loadBundle("CoreBluetooth", globals(),
    bundle_path=objc.pathForFramework(u'/System/Library/Frameworks/IOBluetooth.framework/Versions/A/Frameworks/CoreBluetooth.framework'))


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
