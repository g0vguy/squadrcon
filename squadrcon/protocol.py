import struct
from dataclasses import dataclass

AUTH = 3
AUTH_RESPONSE = 2
EXEC = 2
RESPONSE_VALUE = 0
HEADER_SIZE = 8


@dataclass
class Packet:
    id: int
    type: int
    body: str

    def encode(self) -> bytes:
        body_bytes = self.body.encode("utf-8", errors="replace") + b"\x00\x00"
        payload = struct.pack("<ii", self.id, self.type) + body_bytes
        return struct.pack("<i", len(payload)) + payload


def encode_packet(req_id, ptype, body):
    return Packet(req_id, ptype, body).encode()


def try_decode_packet(buf):
    if len(buf) < 4:
        return None, buf

    size = struct.unpack_from("<i", buf, 0)[0]
    total = 4 + size
    if len(buf) < total:
        return None, buf

    payload = buf[4:total]
    rest = buf[total:]

    if len(payload) < HEADER_SIZE:
        return None, rest

    req_id, ptype = struct.unpack_from("<ii", payload, 0)
    body = payload[HEADER_SIZE:].split(b"\x00", 1)[0].decode("utf-8", errors="replace")
    return Packet(req_id, ptype, body), rest
