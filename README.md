# Meshcore bindings for micropython

Bindings to access your [MeshCore](https://meshcore.co.uk) companion radio nodes on a micropython device.

The meshcore firmware must be configured with serial rx/tx pins connected to the rx/tx pins of the device.

Tested on esp32-s3.

## Example execution

Receiving some messages (before and after getting contacts) then sending back a ping ;)

 <pre>
MPY: soft reboot
b'<\r\x00\x01\x03      mccli'
{'radio_sf': 11, 'adv_type': 1, 'tx_power': 22, 'radio_freq': 869.525, 'adv_lon': -3.42822, 'public_key': '306721e016bec14bd81091641cfba3503ae72c29742e934f72d4800618641c2d', 'radio_bw': 250.0, 'name': 'MeshCoreMicroPythonStack', 'adv_lat': 47.79417, 'max_tx_power': 22, 'radio_cr': 5}
MicroPython v1.24.1 on 2024-11-29; Generic ESP32S3 module with ESP32S3
Type "help()" for more information.
>>> mc.get_msg()
b'<\x01\x00\n'
Received log data
Received log data
Received log data
Msgs are waiting
Received log data
{'path_len': 0, 'code': 8, 'txt_type': 0, 'text': 'mchome: hello', 'channel_idx': 0, 'type': 'CHAN', 'sender_timestamp': 1337018470}
>>> mc.wait_msg()
Received log data
Msgs are waiting
Received log data
Received log data
1
>>> mc.get_msg()
b'<\x01\x00\n'
{'path_len': 0, 'code': 17, 'SNR': 60, 'txt_type': 0, 'channel_idx': 0, 'type': 'CHAN', 'text': 'mchome: Hello everybody', 'sender_timestamp': 3283765350}
>>> mc.get_contacts()
b'<\x01\x00\x04'
{'last_advert': 1743615560, 'type': 3, 'public_key': '23025461ac628964e0c5151dd0b05fb5a3b8a3772a1c15abf493fdce760f1f61', 'adv_lon': -3.428, 'adv_name': 'FdlRoom', 'adv_lat': 47.794, 'lastmod': 1715776659, 'out_path_len': -1, 'flags': 0, 'out_path': b''}
{'last_advert': 1743610210, 'type': 3, 'public_key': '1309e93830d2facf9ebc00e8e4a18d60e8c5140b0aba821921c50fd949cefe4c', 'adv_lon': -3.39648, 'adv_name': 'EnsibsRoom', 'adv_lat': 47.7477, 'lastmod': 1715770587, 'out_path_len': -1, 'flags': 0, 'out_path': b''}
{'last_advert': 1715979297, 'type': 1, 'public_key': 'd78d012b4579d061edbe3cdbcc52c583690d5364136127fc0b45aade676ea4ec', 'adv_lon': -3.428, 'adv_name': 'mchome', 'adv_lat': 47.794, 'lastmod': 1715770982, 'out_path_len': 0, 'flags': 0, 'out_path': b''}
{'last_advert': 1715770351, 'type': 2, 'public_key': 'f7e7cbea642ca5b916c0fe86e4d822cfa017e4c4cbcf8669851d0da91d484c84', 'adv_lon': 0.0, 'adv_name': 'TempNode3', 'adv_lat': 0.0, 'lastmod': 1715772276, 'out_path_len': -1, 'flags': 0, 'out_path': b''}
{'code': 4, 'result': {'FdlRoom': {'last_advert': 1743615560, 'type': 3, 'public_key': '23025461ac628964e0c5151dd0b05fb5a3b8a3772a1c15abf493fdce760f1f61', 'adv_lon': -3.428, 'adv_name': 'FdlRoom', 'adv_lat': 47.794, 'lastmod': 1715776659, 'out_path_len': -1, 'flags': 0, 'out_path': b''}, 'mchome': {'last_advert': 1715979297, 'type': 1, 'public_key': 'd78d012b4579d061edbe3cdbcc52c583690d5364136127fc0b45aade676ea4ec', 'adv_lon': -3.428, 'adv_name': 'mchome', 'adv_lat': 47.794, 'lastmod': 1715770982, 'out_path_len': 0, 'flags': 0, 'out_path': b''}, 'EnsibsRoom': {'last_advert': 1743610210, 'type': 3, 'public_key': '1309e93830d2facf9ebc00e8e4a18d60e8c5140b0aba821921c50fd949cefe4c', 'adv_lon': -3.39648, 'adv_name': 'EnsibsRoom', 'adv_lat': 47.7477, 'lastmod': 1715770587, 'out_path_len': -1, 'flags': 0, 'out_path': b''}, 'TempNode3': {'last_advert': 1715770351, 'type': 2, 'public_key': 'f7e7cbea642ca5b916c0fe86e4d822cfa017e4c4cbcf8669851d0da91d484c84', 'adv_lon': 0.0, 'adv_name': 'TempNode3', 'adv_lat': 0.0, 'lastmod': 1715772276, 'out_path_len': -1, 'flags': 0, 'out_path': b''}}}
>>> mc.get_msg()
b'<\x01\x00\n'
Received log data
Advertisment received
Received log data
Msgs are waiting
{'path_len': 255, 'code': 16, 'SNR': 80, 'pubkey_prefix': 'd78d012b4579', 'txt_type': 0, 'type': 'PRIV', 'text': 'Hey micropy', 'sender_timestamp': 1716042549}
>>> mc.send_msg(bytes.fromhex("d78d012b4579"), "coucou")
b'<\x01\x00\x05'
Received log data
Received log data
b'<\x13\x00\x02\x00\x00\xf7\x9fDf\xd7\x8d\x01+Eycoucou'
{'code': 6, 'type': 0, 'expected_ack': b'b\xc2\xc6\xf3', 'suggested_timeout': 2724}
>>> mc.wait_ack()
Received log data
Received ACK
True
>>> 
</pre>

