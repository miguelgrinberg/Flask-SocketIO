import base64
import json as _json

import six

(OPEN, CLOSE, PING, PONG, MESSAGE, UPGRADE, NOOP) = (0, 1, 2, 3, 4, 5, 6)
packet_names = ['OPEN', 'CLOSE', 'PING', 'PONG', 'MESSAGE', 'UPGRADE', 'NOOP']

binary_types = (six.binary_type, bytearray)


class Packet(object):
    """Engine.IO packet."""

    json = _json

    def __init__(self, packet_type=NOOP, data=None, binary=None,
                 encoded_packet=None):
        self.packet_type = packet_type
        self.data = data
        if binary is not None:
            self.binary = binary
        elif isinstance(data, six.text_type):
            self.binary = False
        elif isinstance(data, binary_types):
            self.binary = True
        else:
            self.binary = False
        if encoded_packet:
            self.decode(encoded_packet)

    def encode(self, b64=False, always_bytes=True):
        """Encode the packet for transmission."""
        if self.binary and not b64:
            encoded_packet = six.int2byte(self.packet_type)
        else:
            encoded_packet = six.text_type(self.packet_type)
            if self.binary and b64:
                encoded_packet = 'b' + encoded_packet
        if self.binary:
            if b64:
                encoded_packet += base64.b64encode(self.data).decode('utf-8')
            else:
                encoded_packet += self.data
        elif isinstance(self.data, six.string_types):
            encoded_packet += self.data
        elif isinstance(self.data, dict) or isinstance(self.data, list):
            encoded_packet += self.json.dumps(self.data,
                                              separators=(',', ':'))
        elif self.data is not None:
            encoded_packet += str(self.data)
        if always_bytes and not isinstance(encoded_packet, binary_types):
            encoded_packet = encoded_packet.encode('utf-8')
        return encoded_packet

    def decode(self, encoded_packet):
        """Decode a transmitted package."""
        b64 = False
        if not isinstance(encoded_packet, binary_types):
            encoded_packet = encoded_packet.encode('utf-8')
        elif not isinstance(encoded_packet, bytes):
            encoded_packet = bytes(encoded_packet)
        self.packet_type = six.byte2int(encoded_packet[0:1])
        if self.packet_type == 98:  # 'b' --> binary base64 encoded packet
            self.binary = True
            encoded_packet = encoded_packet[1:]
            self.packet_type = six.byte2int(encoded_packet[0:1])
            self.packet_type -= 48
            b64 = True
        elif self.packet_type >= 48:
            self.packet_type -= 48
            self.binary = False
        else:
            self.binary = True
        self.data = None
        if len(encoded_packet) > 1:
            if self.binary:
                if b64:
                    self.data = base64.b64decode(encoded_packet[1:])
                else:
                    self.data = encoded_packet[1:]
            else:
                try:
                    self.data = self.json.loads(
                        encoded_packet[1:].decode('utf-8'))
                    if isinstance(self.data, int):
                        # do not allow integer payloads, see
                        # github.com/miguelgrinberg/python-engineio/issues/75
                        # for background on this decision
                        raise ValueError
                except ValueError:
                    self.data = encoded_packet[1:].decode('utf-8')
