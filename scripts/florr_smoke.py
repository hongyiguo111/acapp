"""End-to-end smoke test for the florr mode against a RUNNING local server (scripts/dev.ps1).

Logs in with a real session, opens /wss/florr/ with a raw WebSocket client and checks the protocol.
    .venv\\Scripts\\python.exe scripts\\florr_smoke.py [http://127.0.0.1:8000]
Needs the local test accounts (scripts/make_test_users.py). Uses only the standard library.
"""
import base64
import http.cookiejar
import json
import os
import socket
import struct
import sys
import time
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
HOST, PORT = urllib.parse.urlparse(BASE).hostname, urllib.parse.urlparse(BASE).port or 80


def login(username, password="test1234"):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    q = urllib.parse.urlencode({"username": username, "password": password})
    body = json.loads(opener.open(f"{BASE}/settings/login/?{q}", timeout=10).read())
    assert body["result"] == "success", body
    return "; ".join(f"{c.name}={c.value}" for c in jar)


class WS:
    def __init__(self, cookie=None):
        self.sock = socket.create_connection((HOST, PORT), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode()
        headers = [f"GET /wss/florr/ HTTP/1.1", f"Host: {HOST}:{PORT}", "Upgrade: websocket", "Connection: Upgrade",
                   f"Sec-WebSocket-Key: {key}", "Sec-WebSocket-Version: 13", f"Origin: {BASE}"]
        if cookie:
            headers.append(f"Cookie: {cookie}")
        self.sock.sendall(("\r\n".join(headers) + "\r\n\r\n").encode())
        self.buf = b""
        while b"\r\n\r\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            self.buf += chunk
        head, _, self.buf = self.buf.partition(b"\r\n\r\n")
        self.status = head.split(b"\r\n")[0].decode()

    def send(self, obj):
        data = json.dumps(obj).encode()
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        n = len(data)
        hdr = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n))
        self.sock.sendall(hdr + mask + masked)

    def _need(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError
            self.buf += chunk

    def recv(self):
        """Returns a parsed JSON message, or ('close', code) when the server closes."""
        self._need(2)
        op, ln = self.buf[0] & 0x0F, self.buf[1] & 0x7F
        off = 2
        if ln == 126:
            self._need(4); ln = struct.unpack(">H", self.buf[2:4])[0]; off = 4
        elif ln == 127:
            self._need(10); ln = struct.unpack(">Q", self.buf[2:10])[0]; off = 10
        self._need(off + ln)
        payload, self.buf = self.buf[off:off + ln], self.buf[off + ln:]
        if op == 8:
            return ("close", struct.unpack(">H", payload[:2])[0] if len(payload) >= 2 else None)
        return json.loads(payload) if op == 1 else None


def recv_type(ws, kind, tries=60):
    for _ in range(tries):
        m = ws.recv()
        if isinstance(m, dict) and m.get("t") == kind:
            return m
    raise AssertionError(f"no {kind!r} message")


def check(cond, label):
    print(("PASS  " if cond else "FAIL  ") + label)
    if not cond:
        check.failed = True


check.failed = False

# 1) anonymous connections are refused
anon = WS()
msg = None
try:
    msg = anon.recv()
except Exception:
    pass
check(anon.status.startswith("HTTP/1.1 101") and msg == ("close", 4401) or not anon.status.startswith("HTTP/1.1 101"),
      f"anonymous refused ({anon.status!r}, {msg!r})")

# 2) logged in: welcome first, then snapshots
cookie = login("florr_a")
a = WS(cookie)
check(a.status.startswith("HTTP/1.1 101"), "logged-in handshake")
welcome = a.recv()
check(welcome["t"] == "welcome" and welcome["w"] == 3000, f"welcome first: {welcome['t']}")
check([p["id"] for p in welcome["petals"]] == ["basic", "stinger", "heavy", "rose"], "welcome lists the petal kinds")
inv = recv_type(a, "inv")
check(inv["inv"].get("basic", 0) >= 5 and len(inv["lo"]) == 5, f"inventory message: {inv['inv']} loadout {inv['lo']}")
snap = recv_type(a, "s")
me = next(p for p in snap["ps"] if p["i"] == welcome["id"])
check(snap["t"] == "s" and me["n"] == "florr_a", f"state arrives, my name = {me['n']}")

# 3) movement and petal mode driven by input
x0 = me["x"]
a.send({"t": "in", "dx": 1, "dy": 0, "m": 1})
time.sleep(0.8)
last = None
t_end = time.time() + 0.4
while time.time() < t_end:
    m = a.recv()
    if isinstance(m, dict) and m.get("t") == "s":
        last = m
me2 = next(p for p in last["ps"] if p["i"] == welcome["id"])
moved = me2["x"] - x0
check(moved > 100 or me2["x"] >= 2960, f"moved right by {moved:.0f} units in ~1s (speed 260/s)")
check(me2["r"] > 70, f"petals extended (orbit radius {me2['r']})")

# 4) snapshot rate
t0, count = time.time(), 0
while time.time() - t0 < 1.0:
    m = a.recv()
    if isinstance(m, dict) and m.get("t") == "s":
        count += 1
check(15 <= count <= 25, f"~20 snapshots/s (got {count})")

# 4b) loadout: an unowned kind is refused, unequip/re-equip works and survives a reconnect
original = inv["lo"][:]
a.send({"t": "equip", "slot": 0, "kind": "stinger" if inv["inv"].get("stinger", 0) == 0 else "nonsense"})
refused = recv_type(a, "inv")
check(refused["lo"] == original, "equipping something you do not own is refused")
time.sleep(0.6)
a.send({"t": "equip", "slot": 4, "kind": ""})
unequipped = recv_type(a, "inv")
check(unequipped["lo"][4] == "", f"unequip slot 5 -> {unequipped['lo']}")
a.sock.close()
time.sleep(0.8)                                   # disconnect saves progress
a = WS(login("florr_a"))
welcome = a.recv()
back = recv_type(a, "inv")
check(back["lo"][4] == "", f"loadout persisted across reconnect -> {back['lo']}")
time.sleep(0.6)
a.send({"t": "equip", "slot": 4, "kind": original[4] or "basic"})
restored = recv_type(a, "inv")
check(restored["lo"][4] != "", f"re-equipped -> {restored['lo']}")

# 5) a second account sees the first; a duplicate login replaces the old socket
b = WS(login("florr_b"))
wb = b.recv()
seen = False
for _ in range(10):
    s = b.recv()
    if s["t"] == "s" and any(p["n"] == "florr_a" for p in s["ps"]):
        seen = True
        break
check(wb["t"] == "welcome", "second account joined")
a2 = WS(login("florr_a"))
a2.recv()
closed = None
for _ in range(60):
    m = a.recv()
    if isinstance(m, tuple):
        closed = m
        break
check(closed == ("close", 4409), f"older session of the same account closed with 4409 ({closed})")
print("(second account saw the first one:", seen, "- depends on spawn distance, informational)")

sys.exit(1 if check.failed else 0)
