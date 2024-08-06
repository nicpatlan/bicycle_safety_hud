import serial
import struct
import time

ser = serial.Serial(
    '/dev/ttyACM0',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE
)

def getSpeed():
    try:
        ser.write(bytearray('S', 'utf-8'))
        float_bytes = ser.read(4)
        float_tup = struct.unpack('f', float_bytes)
        return float_tup[0]
    except:
        return 0
