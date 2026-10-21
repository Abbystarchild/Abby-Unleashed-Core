"""Passive serialized integration boundary, with microphone OFF by construction.

No automatic polling, threads, I/O, models, devices, or app integration. A host
injects events and consumes commands. The recording sink is the default.
"""
from collections import deque
from threading import RLock
from typing import Protocol
from duplex_controller import Controller, Style


class CommandSink(Protocol):
    def submit(self, command: dict) -> None:
        """Nonblocking dispatch. Device and worker adapters must recheck epochs."""


class RecordingSink:
    def __init__(self):
        self.commands = deque(maxlen=4096)

    def submit(self, command):
        self.commands.append(command)


class TurnSession:
    EVENTS = frozenset({"begin", "chunk", "submitted_audio", "receipt", "overlap",
                        "pause_receipt", "user_end", "revise_transcript", "classified",
                        "planned", "finished", "stop", "stopped", "tick"})

    def __init__(self, session_id, style=None, sink=None):
        if not session_id:
            raise ValueError("Unique session ID required")
        self.session_id = session_id
        self.controller = Controller(style or Style())
        self.sink = sink if sink is not None else RecordingSink()
        self.microphone_enabled = False
        self.camera_enabled = False
        self._lock = RLock()
        self.audit = deque(maxlen=4096)

    def accepts_output(self, session_id, epoch):
        with self._lock:
            return (session_id == self.session_id and epoch == self.controller.epoch
                    and self.controller.state in {"main", "ack", "clarify", "summary"})

    def asr_identity(self):
        """Snapshot at acoustic onset, before launching an ASR job.

        Capture this once for the job; never relabel a delayed result with the
        current identity. Session IDs must be unique across controller lifetimes.
        """
        with self._lock:
            return dict(session_id=self.session_id,
                        utterance_id=self.controller.utterance_id)

    def asr_onset(self, at, echo="uncertain"):
        """Atomically process onset and capture the identity for its ASR job."""
        with self._lock:
            commands = self.event(self.session_id, "overlap", at=at, echo=echo)
            identity = self.asr_identity() if echo != "echo_only" else None
            return identity, commands

    def event(self, session_id, event, **payload):
        """Host provides monotonic time and ordered events; no polling here.

        Fast-path stop/overlap must reach this owner ahead of slow model callbacks.
        The sink must return immediately; async completions return via event().
        """
        with self._lock:
            if session_id != self.session_id:
                return []
            if event not in self.EVENTS:
                raise ValueError("Unsupported event")
            commands = getattr(self.controller, event)(**payload)
            self.audit.append(dict(event=event, at_ms=payload.get("at"),
                                   epoch=self.controller.epoch))
            enriched = [dict(c, session_id=self.session_id) for c in commands]
            for command in enriched:
                self.sink.submit(command)
            return enriched
