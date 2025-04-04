import select

class SocketCon:
    def __init__(self, socket) :
        self.socket = socket
        self.frame_started = False
        self.frame_size = 0
        self.header = b""
        self.inframe = b""
        self.recvd = []
        self.inputs = [ socket ]
        self.outputs = [ ]

    def recv (self) :
        read, write, ex = select.select(self.inputs, self.outputs, self.inputs, 0.1)

        if len(read) > 0 :
            return self.socket.recv(1024)
        else :
            return b''

    def send (self, data) :
        sz = len(data).to_bytes(2, "little")
        pkt = b"\x3c" + sz + data
        self.socket.sendall (pkt)
        
    def has_response (self) :
        self.uart_rx()
        return len(self.recvd) > 0
    
    def first_response (self) :
        self.uart_rx()
        return self.recvd.pop(0)

    def uart_rx (self) :
        data = self.recv()
        self.handle_rx(data)

    def handle_rx (self, data) :
        headerlen = len(self.header)
        framelen = len(self.inframe)
        if not self.frame_started : # wait start of frame
            if len(data) >= 3 - headerlen:
                self.header = self.header + data[:3-headerlen]
                self.frame_started = True
                self.frame_size = int.from_bytes(self.header[1:], "little")
                self.handle_rx(data[3-headerlen:])
            else:
                self.header = self.header + data
        else:
            if framelen + len(data) < self.frame_size:
                self.inframe = self.inframe + data
            else:
                self.inframe = self.inframe + data[:self.frame_size-framelen]
                self.recvd.append(self.inframe)
                self.frame_started = False
                self.header = b""
                self.inframe = b""
                if framelen + len(data) > self.frame_size:
                    self.handle_rx(data[self.frame_size-framelen:])        
