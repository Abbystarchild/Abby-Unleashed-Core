"""Shared send/close ownership; shutdown can interrupt a blocked send."""
import threading


class SendOwnership:
    def __init__(self, connection, interrupted, error):
        self.connection = connection
        self.interrupted = interrupted
        self.error = error
        self.lock = threading.RLock()
        self.socket = None
        self.original_send = connection.send
        connection.send = self.send

    def require_active(self):
        if self.interrupted():
            raise self.error('Cancelled/deadline before request write')

    def capture(self):
        self.socket = self.connection.sock
        with self.lock:
            self.require_active()

    def send(self, data):
        with self.lock:
            self.require_active()
            if self.connection.sock is None:
                raise self.error('Connection no longer owned')
            self.original_send(data)

    def abort(self):
        # Never wait for a blocked writer before shutting down its socket.
        target = self.socket or self.connection.sock
        if target:
            try:
                target.shutdown(2)
            except OSError:
                pass
        self.close()

    def close(self):
        with self.lock:
            self.connection.close()
