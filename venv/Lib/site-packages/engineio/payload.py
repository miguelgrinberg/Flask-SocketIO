import six

from . import packet


class Payload(object):
    """Engine.IO payload."""
    def __init__(self, packets=None, encoded_payload=None):
        self.packets = packets or []
        if encoded_payload is not None:
            self.decode(encoded_payload)

    def encode(self, b64=False):
        """Encode the payload for transmission."""
        encoded_payload = b''
        for pkt in self.packets:
            encoded_packet = pkt.encode(b64=b64)
            packet_len = len(encoded_packet)
            if b64:
                encoded_payload += str(packet_len).encode('utf-8') + b':' + \
                    encoded_packet
            else:
                binary_len = b''
                while packet_len != 0:
                    binary_len = six.int2byte(packet_len % 10) + binary_len
                    packet_len = int(packet_len / 10)
                if not pkt.binary:
                    encoded_payload += b'\0'
                else:
                    encoded_payload += b'\1'
                encoded_payload += binary_len + b'\xff' + encoded_packet
        return encoded_payload

    def decode(self, encoded_payload):
        """Decode a transmitted payload."""
        self.packets = []
        while encoded_payload:
            if six.byte2int(encoded_payload[0:1]) <= 1:
                packet_len = 0
                i = 1
                while six.byte2int(encoded_payload[i:i + 1]) != 255:
                    packet_len = packet_len * 10 + six.byte2int(
                        encoded_payload[i:i + 1])
                    i += 1
                self.packets.append(packet.Packet(
                    encoded_packet=encoded_payload[i + 1:i + 1 + packet_len]))
            else:
                i = encoded_payload.find(b':')
                if i == -1:
                    raise ValueError('invalid payload')

                # extracting the packet out of the payload is extremely
                # inefficient, because the payload needs to be treated as
                # binary, but the non-binary packets have to be parsed as
                # unicode. Luckily this complication only applies to long
                # polling, as the websocket transport sends packets
                # individually wrapped.
                packet_len = int(encoded_payload[0:i])
                pkt = encoded_payload.decode('utf-8', errors='ignore')[
                    i + 1: i + 1 + packet_len].encode('utf-8')
                self.packets.append(packet.Packet(encoded_packet=pkt))

                # the engine.io protocol sends the packet length in
                # utf-8 characters, but we need it in bytes to be able to
                # jump to the next packet in the payload
                packet_len = len(pkt)
            encoded_payload = encoded_payload[i + 1 + packet_len:]
