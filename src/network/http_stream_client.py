"""
HTTP transport for real-time telemetry.

POSTs gzipped frame batches to /telemetry/stream/<session>. Same interface as
WebSocketClient, so the app can use either: the server runs every frame through
the same pipeline. Plain HTTPS works on hosting that can't hold a socket open,
and frames are kept through short network drops instead of being lost.
"""

import gzip
import json
import threading
import time

import requests


class HttpStreamClient:
    SEND_EVERY = 1.0            # seconds between uploads
    MAX_PER_POST = 1200         # server-side limit per request
    MAX_BACKLOG = 120 * 120     # ~2 minutes at 120 Hz kept through a network drop
    MAX_BACKOFF = 15.0

    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self.connected = False
        self.running = False
        self.thread = None
        self.dropped = 0
        self._pending = []
        self._lock = threading.Lock()       # guards _pending
        self._send_lock = threading.Lock()  # one upload at a time (uploader vs. final flush)
        self._next_seq = 0                  # per-frame sequence, lets the server drop retried duplicates

    @property
    def is_connected(self) -> bool:
        return self.connected

    def connect(self) -> bool:
        """Probe with an empty batch. True if the server speaks this transport."""
        try:
            resp = self._post([])
        except Exception as e:
            print(f"HTTP stream probe failed: {e}")
            return False
        if resp.status_code != 200:
            print(f"HTTP stream not available ({resp.status_code})")
            return False
        self.connected = True
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return True

    def send_batch(self, frames: list):
        if not frames:
            return
        with self._lock:
            for frame in frames:
                numbered = dict(frame)  # don't write into the caller's frame
                numbered['_seq'] = self._next_seq
                self._next_seq += 1
                self._pending.append(numbered)
            over = len(self._pending) - self.MAX_BACKLOG
            if over > 0:
                del self._pending[:over]
                self.dropped += over

    def send_telemetry(self, data: dict):
        self.send_batch([data])

    def disconnect(self):
        """Stop the uploader and flush what's left (bounded), so the last lap lands."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=self.SEND_EVERY + 1)
        deadline = time.time() + 10
        while time.time() < deadline:
            with self._lock:
                if not self._pending:
                    break
            if not self._send_once():
                break
        self.connected = False

    def _post(self, frames: list):
        body = gzip.compress(json.dumps({'frames': frames}).encode('utf-8'))
        return requests.post(
            self.url,
            data=body,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Content-Encoding': 'gzip',
            },
            verify=False, timeout=15,
        )

    def _run(self):
        wait = self.SEND_EVERY
        while self.running:
            time.sleep(wait)
            wait = self.SEND_EVERY if self._send_once() else min(wait * 2, self.MAX_BACKOFF)

    def _send_once(self) -> bool:
        """Upload the oldest chunk. False means 'try again later' (network/server trouble)."""
        with self._send_lock:
            return self._send_chunk()

    def _send_chunk(self) -> bool:
        with self._lock:
            chunk = self._pending[:self.MAX_PER_POST]
        if not chunk:
            return True
        try:
            resp = self._post(chunk)
        except Exception:
            return False
        if resp.status_code == 200:
            self._drop_through(chunk[-1]['_seq'])
            return True
        if resp.status_code in (400, 401, 403, 404, 413):
            # Retrying won't help: drop the chunk so the rest can flow.
            print(f"HTTP stream rejected {len(chunk)} frames ({resp.status_code}): {resp.text[:120]}")
            self._drop_through(chunk[-1]['_seq'])
            with self._lock:
                self.dropped += len(chunk)
            if resp.status_code in (401, 403, 404):
                self.connected = False
            return True
        return False

    def _drop_through(self, seq: int):
        """Remove frames up to and including `seq`. By number, not count: the
        backlog may have been trimmed from the front while this chunk was in flight."""
        with self._lock:
            i = 0
            while i < len(self._pending) and self._pending[i]['_seq'] <= seq:
                i += 1
            del self._pending[:i]
