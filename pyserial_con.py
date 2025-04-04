class SerialCon:
    def __init__(self, uart) :
        self.uart = uart
        self.frame_started = False
        self.frame_size = 0
        self.header = b""
        self.inframe = b""
        self.recvd = []

    def recv (self) :
        len = self.uart.inWaiting()
        if len > 0:
            return self.uart.read(len)
        else :
            return b''

    def send (self, data) :
        sz = len(data).to_bytes(2, "little")
        pkt = b"\x3c" + sz + data
        self.uart.write (pkt)
        
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
