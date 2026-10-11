"""Minimal RCON client for the local Angel Attack server.

    python tools\\rcon.py "list" "time query daytime"
"""
import os, socket, struct, sys

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server")


def server_properties():
    props = {}
    for line in open(os.path.join(SERVER, "server.properties"), encoding="utf-8"):
        if "=" in line and not line.startswith("#"):
            k, v = line.rstrip("\n").split("=", 1)
            props[k] = v
    return props


class Rcon:
    def __init__(self, host="127.0.0.1", port=None, password=None, timeout=20):
        props = server_properties()
        self.sock = socket.create_connection((host, int(port or props.get("rcon.port", 25576))), timeout=timeout)
        self._send(3, password or props["rcon.password"])
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
        self.sock.close()


if __name__ == "__main__":
    r = Rcon()
    for c in sys.argv[1:]:
        print(f"> {c}\n{r.cmd(c)}")
    r.close()
