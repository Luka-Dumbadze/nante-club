import socket
import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("ecr")

STX, ETX, ACK, NAK, FS = 0x02, 0x03, 0x06, 0x15, 0x1C
PROTOCOL_VERSION, MSG_CLASS_REQUEST, MSG_CLASS_RESPONSE = "104", "0", "1"
MSGTYPE_HOLD, MSGTYPE_SALE = "01", "10"
ERRCODE_IGNORE, ERRCODE_OK = "999", "000"
FIELD_AMOUNT, FIELD_APPROVAL, FIELD_CURRENCY, FIELD_TERMINAL_ID = "B", "F", "T", "Q"
CURRENCY_GEL = "981"
LRC_INIT, LRC_INCLUDE_STX, LRC_INCLUDE_ETX = 0x00, False, True

def calculate_lrc(payload: bytes, *, init: int = LRC_INIT) -> int:
    lrc = init & 0xFF
    for b in payload: lrc ^= b
    return lrc & 0xFF

def _lrc_cover(body: bytes) -> bytes:
    cover = bytearray()
    if LRC_INCLUDE_STX: cover.append(STX)
    cover += body
    if LRC_INCLUDE_ETX: cover.append(ETX)
    return bytes(cover)

def wrap_frame(body: bytes) -> bytes:
    return bytes([STX]) + body + bytes([ETX, calculate_lrc(_lrc_cover(body))])

def build_header(msg_type: str, txn_number: int) -> bytes:
    return f"{PROTOCOL_VERSION}{MSG_CLASS_REQUEST}{msg_type}{ERRCODE_IGNORE}{txn_number:03d}".encode("ascii")

def build_sale_body(amount_minor: int, txn_number: int) -> bytes:
    header = build_header(MSGTYPE_SALE, txn_number)
    return header + bytes([FS]) + FIELD_AMOUNT.encode() + str(amount_minor).encode() + bytes([FS]) + FIELD_CURRENCY.encode() + CURRENCY_GEL.encode()

@dataclass
class EcrResponse:
    raw: bytes
    version: str
    msg_class: str
    msg_type: str
    error_code: str
    txn_number: int
    fields: dict = field(default_factory=dict)
    @property
    def approved(self) -> bool: return self.error_code == ERRCODE_OK

def parse_message(body: bytes) -> EcrResponse:
    text = body.decode("ascii", errors="replace")
    header, rest = text[:12], text[12:]
    resp = EcrResponse(raw=body, version=header[0:3], msg_class=header[3:4], msg_type=header[4:6], error_code=header[6:9], txn_number=int(header[9:12]))
    for chunk in rest.split(chr(FS)):
        if chunk: resp.fields[chunk[0]] = chunk[1:].rstrip(" ")
    return resp

class EcrTerminalClient:
    def __init__(self, host: str, port: int):
        self.host, self.port, self._sock = host, port, None

    def connect(self):
        self._sock = socket.create_connection((self.host, self.port), timeout=5.0)
        self._sock.settimeout(3.0)

    def close(self):
        if self._sock: self._sock.close(); self._sock = None

    def __enter__(self): self.connect(); return self
    def __exit__(self, *exc): self.close()

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk: raise ConnectionError("Terminal closed connection")
            buf += chunk
        return bytes(buf)

    def _read_frame(self, timeout: float) -> bytes:
        self._sock.settimeout(timeout)
        while self._recv_exact(1)[0] != STX: pass
        body = bytearray()
        while True:
            b = self._recv_exact(1)[0]
            if b == ETX: break
            body.append(b)
        lrc_received = self._recv_exact(1)[0]
        if lrc_received != calculate_lrc(_lrc_cover(bytes(body))):
            self._sock.sendall(bytes([NAK]))
            raise ValueError("Bad LRC")
        self._sock.sendall(bytes([ACK]))   
        return bytes(body)

    def _send_with_ack(self, frame: bytes):
        for _ in range(3):
            self._sock.settimeout(3.0)
            self._sock.sendall(frame)
            try: resp = self._recv_exact(1)[0]
            except socket.timeout: continue
            if resp == ACK: return
            if resp == NAK: continue
            raise ValueError(f"Unexpected byte 0x{resp:02X}")
        raise ConnectionError("No ACK")

    def sale(self, amount_minor: int, txn_number: int) -> EcrResponse:
        self._send_with_ack(wrap_frame(build_sale_body(amount_minor, txn_number)))
        while True:
            msg = parse_message(self._read_frame(120.0))
            if msg.msg_type != MSGTYPE_HOLD: return msg