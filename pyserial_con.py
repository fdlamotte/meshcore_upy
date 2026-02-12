class SerialCon:
    def __init__(self, uart) :
        self.uart = uart
        self.frame_expected_size = 0
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

    def handle_rx(self, data):
        if len(self.header) == 0: # did not find start of frame yet
            # search start of frame (0x3e) in data
            idx = data.find(b"\x3e")
            if idx < 0: # no start of frame
                return
            self.header = data[0:1]
            data = data[1:]

        if len(self.header) < 3: # header not complete yet
            while len(self.header) < 3 and len(data) > 0:
                self.header = self.header + data[0:1]
                data = data[1:]
            if len(self.header) < 3: # still not complete
                return

            # get size and check
            self.frame_expected_size = int.from_bytes(self.header[1:], "little", signed=False)
            if self.frame_expected_size > 300 : # invalid size
                # reset inframe
                self.header = b""
                self.inframe = b""
                self.frame_expected_size = 0
                if len(data) > 0: # rerun handle_rx on remaining data
                    self.handle_rx(data)
                    return

        if len(data) + len(self.inframe) < self.frame_expected_size:
            self.inframe = self.inframe + data
            # frame not complete, wait for next rx
            return

        upbound = self.frame_expected_size - len(self.inframe)
        self.inframe = self.inframe + data[0:upbound]
        data = data[upbound:]
        self.recvd.append(self.inframe)
        # reset inframe
        self.inframe = b""
        self.header = b""
        self.frame_expected_size = 0
        if len(data) > 0: # rerun handle_rx on remaining data
            self.handle_rx(data)
