# Tests of the Amiacs Light Controller device.

import smbus

bus = smbus.SMBus(1)

amiacsLightControllerAddress = 0x07

def setAmbientColor_Should():
    bus.write_i2c_block_data(amiacsLightControllerAddress, 0, [15, 23, 255])

    return



setAmbientColor()