# Testing the communication between Raspberry Pi and Arduino using I2C.

import smbus
import time

# for RPI version 1, use "bus = smbus.SMBus(0)"
bus = smbus.SMBus(1)

# This is the address we setup in the Arduino Program
address = 0x07

def writeNumber(value):
    bus.write_byte(address, value)
    time.sleep(1)
    bus.write_i2c_block_data(address, value, [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])

    # bus.write_byte_data(address, 0, value)
    return -1

def readNumber():
    number = bus.read_byte(address)

    # number = bus.read_byte_data(address, 1)
    return number

while True:
    var = int(input("Enter 1 – 9: "))
    if not var:
        continue
    writeNumber(var)
    print("RPI: Hi Arduino, I sent you ", var)

    # sleep one second
    time.sleep(1)
    number = readNumber()
    print("Arduino: Hey RPI, I received a digit ", number)
    print()

