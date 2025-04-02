""" 
    mccli.py : CLI interface to MeschCore BLE companion app
"""
import time
from machine import UART
from ustruct import unpack

def printerr (s) :
    print(s)

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
        print(pkt)
        
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

class MeshCore:
    """
    Interface to a BLE MeshCore device
    """
    self_info={}
    contacts={}

    def __init__(self, cx):
        """ Constructor : specify address """
        self.time = 0
        self.contact_nb = 0
        self.last_status = None
        self.cx = cx
        self.msgs = 0
        self.ack = False
        self.last_status = None
        self.login = True

    def connect(self) :
        self.send_appstart()

    def handle_rx(self, data: bytearray):
        """ Callback to handle received data """
        res = {}
        arg = data[0]
        res["code"] = arg 
        if arg == 0: # ok
            if len(data) == 5 :  # an integer
                res["result"] = int.from_bytes(data[1:5], 'little')
            else:
                res["result"] = True
        elif arg == 1: # error
            if len(data) > 1:
                res["error_code"] = data[1]
                res["result"] = False # error code if fw > 1.4
            else:
                res["result"] = False
        elif arg == 2: # contact start
            self.contact_nb = int.from_bytes(data[1:5], 'little')
            self.contacts={}
        elif arg == 3: # contact
            c = {}
            c["public_key"] = data[1:33].hex()
            c["type"] = data[33]
            c["flags"] = data[34]
            c["out_path_len"] = unpack("<b", data[35:36])[0]
            plen = unpack("<b", data[35:36])[0]
            if plen == -1 or plen == 255: 
                plen = 0
            c["out_path"] = data[36:36+plen].hex()
            c["adv_name"] = data[100:132].decode().replace("\0","")
            c["last_advert"] = int.from_bytes(data[132:136], 'little')
            c["adv_lat"] = unpack("<i", data[136:140])[0]/1e6
            c["adv_lon"] = unpack("<i", data[140:144])[0]/1e6
            c["lastmod"] = int.from_bytes(data[144:148], 'little')
            self.contacts[c["adv_name"]]=c
            res["result"] = c
            print(c)
        elif arg == 4: # end of contacts
            res["result"] = self.contacts
        elif arg == 5: # self info
            self.self_info["adv_type"] = data[1]
            self.self_info["tx_power"] = data[2]
            self.self_info["max_tx_power"] = data[3]
            self.self_info["public_key"] = data[4:36].hex()
            self.self_info["adv_lat"] = unpack("<i", data[36:40])[0]/1e6
            self.self_info["adv_lon"] = unpack("<i", data[40:44])[0]/1e6
            #self.self_info["reserved_44:48"] = data[44:48].hex()
            self.self_info["radio_freq"] = int.from_bytes(data[48:52], "little" ) / 1000
            self.self_info["radio_bw"] = int.from_bytes(data[52:56], "little") / 1000
            self.self_info["radio_sf"] = data[56]
            self.self_info["radio_cr"] = data[57]
            self.self_info["name"] = data[58:].decode()
            print(self.self_info)
            res["result"] = self.self_info
        elif arg == 6: # msg sent
            res["type"] = data[1]
            res["expected_ack"] = bytes(data[2:6])
            res["suggested_timeout"] = int.from_bytes(data[6:10], "little")
        elif arg == 7: # contact msg recv
            res["type"] = "PRIV"
            res["pubkey_prefix"] = data[1:7].hex()
            res["path_len"] = data[7]
            res["txt_type"] = data[8]
            res["sender_timestamp"] = int.from_bytes(data[9:13], "little" )
            if data[8] == 2 : # signed packet
                res["signature"] = data[13:17].hex()
                res["text"] = data[17:].decode()
            else :
                res["text"] = data[13:].decode()
                self.msgs = self.msgs - 1
            if self.msgs < 0 :
                self.msgs = 0
        elif arg == 16: # a reply to CMD_SYNC_NEXT_MESSAGE (ver >= 3)
            res["type"] = "PRIV"
            res["SNR"] = int.from_bytes(data[1:2], 'little', True) * 4;
            res["pubkey_prefix"] = data[4:10].hex()
            res["path_len"] = data[10]
            res["txt_type"] = data[11]
            res["sender_timestamp"] = int.from_bytes(data[12:16], "little" )
            if data[11] == 2 : # signed packet
                res["signature"] = data[16:20].hex()
                res["text"] = data[20:].decode()
            else :
                res["text"] = data[16:].decode()
            self.msgs = self.msgs - 1
            if self.msgs < 0 :
                self.msgs = 0
        elif arg == 8 : # chanel msg recv
            res["type"] = "CHAN"
            res["channel_idx"] = data[1]
            res["path_len"] = data[2]
            res["txt_type"] = data[3]
            res["sender_timestamp"] = int.from_bytes(data[4:8], )
            res["text"] = data[8:].decode()
            self.msgs = self.msgs - 1
            if self.msgs < 0 :
                self.msgs = 0
        elif arg == 17: # a reply to CMD_SYNC_NEXT_MESSAGE (ver >= 3)
            res["type"] = "CHAN"
            res["SNR"] = int.from_bytes(data[1:2], 'little', True) * 4;
            res["channel_idx"] = data[4]
            res["path_len"] = data[5]
            res["txt_type"] = data[6]
            res["sender_timestamp"] = int.from_bytes(data[7:11])
            res["text"] = data[11:].decode()
            self.msgs = self.msgs - 1
            if self.msgs < 0 :
                self.msgs = 0
        elif arg == 9: # current time
            res["result"] = int.from_bytes(data[1:5], "little")
        elif arg == 10: # no more msgs
            res["result"] = False
        elif arg == 11: # contact
            res["result"] = "meshcore://" + data[1:].hex()
        elif arg == 12: # battery voltage
            res["result"] = int.from_bytes(data[1:2])
        elif arg == 13: # device info
            print("received device info")
            res["fw ver"] = data[1]
            if data[1] >= 3:
                res["max_contacts"] = data[2] * 2
                res["max_channels"] = data[3]
                res["ble_pin"] = int.from_bytes(data[4:8], )
                res["fw_build"] = data[8:20].decode().replace("\0","")
                res["model"] = data[20:60].decode().replace("\0","")
                res["ver"] = data[60:80].decode().replace("\0","")
            print (res)
        elif arg == 50: # cli response
            res["response"] = data[1:].decode()
        # push notifications
        elif arg == 0x80:
            printerr ("Advertisment received")
        elif arg == 0x81:
            printerr ("Code path update")
        elif arg == 0x82:
            printerr ("Received ACK")
            self.ack = True
        elif arg == 0x83:
            printerr ("Msgs are waiting")
            self.msgs = self.msgs + 1
        elif arg == 0x84:
            printerr ("Received raw data")
            res["SNR"] = data[1] / 4
            res["RSSI"] = data[2]
            res["payload"] = data[4:].hex()
            print(res)
        elif arg == 0x85:
            printerr ("Login success")
            self.login = True
        elif arg == 0x86:
            printerr ("Login failed")
        elif arg == 0x87:
            res["pubkey_pre"] = data[2:8].hex()
            res["bat"] = int.from_bytes(data[8:10], )
            res["tx_queue_len"] = int.from_bytes(data[10:12], )
            res["free_queue_len"] = int.from_bytes(data[12:14], )
            res["last_rssi"] = int.from_bytes(data[14:16], 'little', True)
            res["nb_recv"] = int.from_bytes(data[16:20], 'little', False)
            res["nb_sent"] = int.from_bytes(data[20:24], 'little', False)
            res["airtime"] = int.from_bytes(data[24:28], )
            res["uptime"] = int.from_bytes(data[28:32], )
            res["sent_flood"] = int.from_bytes(data[32:36], )
            res["sent_direct"] = int.from_bytes(data[36:40], )
            res["recv_flood"] = int.from_bytes(data[40:44], )
            res["recv_direct"] = int.from_bytes(data[44:48], )
            res["full_evts"] = int.from_bytes(data[48:50], )
            res["last_snr"] = int.from_bytes(data[50:52], 'little', True) / 4
            res["direct_dups"] = int.from_bytes(data[52:54], )
            res["flood_dups"] = int.from_bytes(data[54:56], )
            #self.status_resp.set_result(res)
            self.last_status=res;
            #printerr(res)
        elif arg == 0x88:
            printerr ("Received log data")
        elif arg == _:
            printerr (f"Unhandled data received {data}")

        return res

    def process_input(self):
        while self.cx.has_response() :
            rx = self.cx.first_response()
            self.handle_rx(rx)

    def next_response(self):
        res = None
        while res is None or res["code"] >= 0x80 :
            while not self.cx.has_response():
                time.sleep(0.01)

            rx = self.cx.first_response()
            res = self.handle_rx(rx)
        return res

    def send(self, data, timeout = 5):
        """ Helper function to synchronously send (and receive) data to the node """
        self.cx.send(data)
        return self.next_response()
            
    def send_only(self, data): # don't wait reply
        self.cx.send(data)

    def send_appstart(self):
        """ Send APPSTART to the node """
        b1 = bytearray(b'\x01\x03      mccli')
        return self.send(b1)

    def send_device_qeury(self):
        return self.send(b"\x16\x03");

    def send_advert(self):
        """ Make the node send an advertisement """
        return self.send(b"\x07")

    def set_name(self, name):
        """ Changes the name of the node """
        return self.send(b'\x08' + name.encode("ascii"))

    def set_coords(self, lat, lon):
        return self.send(b'\x0e'\
                + int(lat*1e6).to_bytes(4, 'little', True)\
                + int(lon*1e6).to_bytes(4, 'little', True)\
                + int(0).to_bytes(4, 'little'))

    def reboot(self):
        self.send_only(b'\x13reboot')
        return True

    def get_bat(self):
        return self.send(b'\x14')

    def get_time(self):
        """ Get the time (epoch) of the node """
        res = self.send(b"\x05")
        self.time = res["result"]
        return self.time

    def set_time(self, val):
        """ Sets a new epoch """
        return self.send(b"\x06" + int(val).to_bytes(4, 'little'))

    def set_tx_power(self, val):
        """ Sets tx power """
        return self.send(b"\x0c" + int(val).to_bytes(4, 'little'))

    def set_radio (self, freq, bw, sf, cr):
        """ Sets radio params """
        return self.send(b"\x0b" \
                + int(float(freq)*1000).to_bytes(4, 'little')\
                + int(float(bw)*1000).to_bytes(4, 'little')\
                + int(sf).to_bytes(1, 'little')\
                + int(cr).to_bytes(1, 'little'))

    def set_tuning (self, rx_dly, af):
        """ Sets radio params """
        return self.send(b"\x15" \
                + int(rx_dly).to_bytes(4, 'little')\
                + int(af).to_bytes(4, 'little')\
                + int(0).to_bytes(1, 'little')\
                + int(0).to_bytes(1, 'little'))

    def set_devicepin (self, pin):
        return self.send(b"\x25" \
                + int(pin).to_bytes(4, 'little'))

    def get_contacts(self):
        """ Starts retreiving contacts """
        self.send(b"\x04")
        res = None
        while res is None or res["code"] != 4 :
            res = self.next_response()
        return res

    def ensure_contacts(self):
        if len(self.contacts) == 0 :
            self.get_contacts()

    def reset_path(self, key):
        data = b"\x0D" + key
        return self.send(data)

    def share_contact(self, key):
        data = b"\x10" + key
        return self.send(data)

    def export_contact(self, key=b""):
        data = b"\x11" + key
        return self.send(data)

    def remove_contact(self, key):
        data = b"\x0f" + key
        return self.send(data)

    def set_out_path(self, contact, path):
        contact["out_path"] = path
        contact["out_path_len"] = -1
        contact["out_path_len"] = int(len(path) / 2)

    def update_contact(self, contact):
        out_path_hex = contact["out_path"]
        out_path_hex = out_path_hex + (128-len(out_path_hex)) * "0" 
        adv_name_hex = contact["adv_name"].encode().hex()
        adv_name_hex = adv_name_hex + (64-len(adv_name_hex)) * "0"
        data = b"\x09" \
            + bytes.fromhex(contact["public_key"])\
            + contact["type"].to_bytes(1)\
            + contact["flags"].to_bytes(1)\
            + contact["out_path_len"].to_bytes(1, 'little', True)\
            + bytes.fromhex(out_path_hex)\
            + bytes.fromhex(adv_name_hex)\
            + contact["last_advert"].to_bytes(4, 'little')\
            + int(contact["adv_lat"]*1e6).to_bytes(4, 'little', True)\
            + int(contact["adv_lon"]*1e6).to_bytes(4, 'little', True)
        return self.send(data)

    def send_login(self, dst, pwd):
        self.login = None
        data = b"\x1a" + dst + pwd.encode("ascii")
        return self.send(data)

    def wait_login(self, timeout = 5):
        self.process_input()
        while not self.login and tries < 10 * timeout:
            time.sleep(0.1)
            tries = tries + 1
            self.process_input()
        return self.login

    def send_statusreq(self, dst):
        self.last_status = None
        data = b"\x1b" + dst
        return self.send(data)

    def wait_status(self, timeout = 5):
        self.process_input()
        while self.last_status is None and tries < 10 * timeout:
            time.sleep(0.1)
            tries = tries + 1
            self.process_input()
        return self.last_status
        
    def send_cmd(self, dst, cmd):
        """ Send a cmd to a node """
        timestamp = (self.get_time()).to_bytes(4, 'little')
        data = b"\x02\x01\x00" + timestamp + dst + cmd.encode("ascii")
        #self.ack_ev.clear() # no ack ?
        return self.send(data)

    def send_msg(self, dst, msg):
        """ Send a message to a node """
        timestamp = (self.get_time()).to_bytes(4, 'little')
        data = b"\x02\x00\x00" + timestamp + dst + msg.encode("ascii")
        self.ack = False
        return self.send(data)

    def send_chan_msg(self, chan, msg):
        """ Send a message to a public channel """
        timestamp = (self.get_time()).to_bytes(4, 'little')
        data = b"\x03\x00" + chan.to_bytes(1, 'little') + timestamp + msg.encode("ascii")
        return self.send(data)

    def get_msg(self):
        """ Get message from the node (stored in queue) """
        res = self.send(b"\x0A", 1)
        return res

    def wait_msg(self, timeout=-1):
        """ Wait for a message """
        tries = 0
        self.process_input()
        while (timeout == -1 or tries < 10 * timeout)\
              and self.msgs == 0 :
            time.sleep(0.1)
            tries = tries + 1
            self.process_input()
        
        return self.msgs

    def wait_ack(self, timeout=6):
        """ Wait ack """
        tries = 0
        self.process_input()
        while self.ack == False and tries < 10 * timeout:
            time.sleep(0.1)
            tries = tries + 1
            self.process_input()
        return self.ack

    def send_cli(self, cmd):
        data = b"\x32" + cmd.encode('ascii')
        return self.send(data)


