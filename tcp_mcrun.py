import socket
from socket_con import SocketCon
from meshcore import MeshCore

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("mchome", 5000))

sc = SocketCon(sock)
mc = MeshCore(sc)
mc.connect()
