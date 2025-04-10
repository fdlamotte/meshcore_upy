from machine import UART
from userial_con import SerialCon
from meshcore import MeshCore
import time

uart2 = UART(2, baudrate=115200, tx=3, rx=2)
sc = SerialCon(uart2)
mc = MeshCore(sc)
mc.connect()

