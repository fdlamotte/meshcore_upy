from machine import UART

class SerialCon:
    def __init__(self, uart) :
        self.uart = uart
        self.frame_started = False
        self.frame_size = 0
        self.header = b""
        self.inframe = b""
        self.recvd = []
        self.uart.irq(handler=self.uart_rx, trigger=UART.IRQ_RXIDLE)

    def recv (self) :
        return self.uart.read()

    def send (self, data) :
        sz = len(data).to_bytes(2, "little")
        pkt = b"\x3c" + sz + data
        self.uart.write (pkt)
        
    def has_response (self) :
        return len(self.recvd) > 0
    
    def first_response (self) :
        return self.recvd.pop(0)

    def uart_rx (self, uart) :
        data = uart.read()
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
