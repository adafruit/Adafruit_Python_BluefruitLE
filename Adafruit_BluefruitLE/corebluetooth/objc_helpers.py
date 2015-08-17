# Objective-C helper functions to convert between Python and Objective-C types.
# Author: Tony DiCola
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
