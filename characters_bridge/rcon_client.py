"""Minimal RCON client for the Angel Attack server (same protocol code as Genesis, its own server.properties).

Host/port/password come from D:\\angel-attack\\server\\server.properties, or ANGEL_RCON_HOST / ANGEL_RCON_PORT /
ANGEL_RCON_PASSWORD. The password is never printed.
"""
import os
import socket
import struct
import threading
import time

from config import SERVER_DIR


def server_properties():
    props = {}
    path = os.path.join(SERVER_DIR, "server.properties")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if "=" in line and not line.startswith("#"):
                k, v = line.rstrip("\r\n").split("=", 1)
                props[k] = v
    return props


class Rcon:
    def __init__(self, host=None, port=None, password=None, timeout=20):
        props = server_properties()
        host = host or os.environ.get("ANGEL_RCON_HOST", "127.0.0.1")
        port = int(port or os.environ.get("ANGEL_RCON_PORT") or props.get("rcon.port", 25575))
        password = password or os.environ.get("ANGEL_RCON_PASSWORD") or props.get("rcon.password")
        if not password:
            raise PermissionError("no RCON password (server.properties has none and ANGEL_RCON_PASSWORD is not set)")
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self._send(3, password)
        if self._recv()[0] == -1:
            raise PermissionError("RCON password rejected")

    def _send(self, kind, body, ident=7):
        data = struct.pack("<ii", ident, kind) + body.encode("utf-8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(data)) + data)

    def _read(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("server closed the connection")
            buf += chunk
        return buf

    def _recv(self):
        size = struct.unpack("<i", self._read(4))[0]
        data = self._read(size)
        ident, kind = struct.unpack("<ii", data[:8])
        return ident, data[8:-2].decode("utf-8", "replace")

    def cmd(self, command):
        self._send(2, command)
        return self._recv()[1]

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class ReconnectingRcon:
    """Thread-safe; reconnects once if the connection dropped; retries connecting until the server is up."""

    def __init__(self, wait_for_server=True):
        self.lock = threading.RLock()
        self.r = None
        self.connect(wait_for_server)

    def connect(self, wait=True):
        announced = False
        while True:
            try:
                self.r = Rcon()
                return
            except (OSError, ConnectionError) as e:
                if not wait:
                    raise
                if not announced:
                    print(f"[rcon] waiting for the server ({e.__class__.__name__}) ...", flush=True)
                    announced = True
                time.sleep(2)

    def cmd(self, command):
        with self.lock:
            try:
                return self.r.cmd(command)
            except (OSError, ConnectionError):
                self.r.close()
                self.connect(True)
                return self.r.cmd(command)


if __name__ == "__main__":      # python rcon_client.py "scoreboard players get #beat angel.story"
    import sys
    c = Rcon()
    for line in sys.argv[1:]:
        print(f"> {line}\n{c.cmd(line)}")
    c.close()
