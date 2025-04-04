import serial
from pyserial_con import SerialCon
from meshcore import MeshCore
import time

uart = serial.Serial('/dev/ttyS0', 115200, timeout=0)
sc = SerialCon(uart)
mc = MeshCore(sc)
mc.connect()

