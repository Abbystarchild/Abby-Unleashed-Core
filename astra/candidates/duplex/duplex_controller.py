"""Pure deterministic turn policy. No device, model, network, or clock access.

Feed events serially from one owner. Times are monotonic milliseconds; adapter
commands are data, never executed here. See DUPLEX_INTEGRATION.md.
"""
from dataclasses import dataclass, field
from math import isfinite


@dataclass(frozen=True)
class Style:
    profile: str = "Astra"
    disruption: str = "yield"
    summary_ms: int = 1200
    confidence: float = 0.8
    classify_timeout_ms: int = 1500
    topic_ttl_ms: int = 30000

    def __post_init__(self):
        if self.disruption not in {"yield", "summary"}:
            raise ValueError("Unknown disruption policy")
        if not 0 <= self.summary_ms <= 1500 or not 0.5 <= self.confidence <= 1:
            raise ValueError("Unsafe policy bounds")
        if not 1 <= self.classify_timeout_ms <= 5000:
            raise ValueError("Invalid classification timeout")
        if not 1 <= self.topic_ttl_ms <= 120000:
            raise ValueError("Invalid topic expiry")


@dataclass(frozen=True)
class Chunk:
    semantic_id: str
    text: str
    duration_ms: int


@dataclass
class Controller:
    style: Style = field(default_factory=Style)
    epoch: int = 0
    state: str = "listening"
    speaking_user: bool = False
    cursor: dict | None = None
    context: str = ""
    now: int = -1
    pending_pause: int | None = None
    decision: str | None = None
    classify_deadline: int | None = None
    summary_deadline: int | None = None
    chunks: dict = field(default_factory=dict)
    played: dict = field(default_factory=dict)
    modes: dict = field(default_factory=dict)
    metrics: list = field(default_factory=list)
    topic_expires: int | None = None
    transcript: str = ""
    intent: str | None = None
    submitted: set = field(default_factory=set)
    asr_revision: int = -1

    def _time(self, at):
        if not isinstance(at, int) or at < self.now:
            raise ValueError("Events require monotonic integer milliseconds")
        self.now = at

    def _command(self, kind, **data):
        return dict(kind=kind, epoch=self.epoch, at_ms=self.now, **data)

    def _stage(self, mode):
        self.epoch += 1
        self.state = mode
        self.modes[self.epoch] = mode
        self.chunks = {self.epoch: []}
        self.played = {self.epoch: (-1, 0)}
        self.submitted.clear()

    def begin(self, at, context):
        self._time(at)
        if self.state != "listening" or self.speaking_user:
            raise ValueError("Cannot take floor while occupied")
        self.cursor = None
        self.context = context
        self.topic_expires = None
        self._stage("main")
        return [self._command("generate", context=context, profile=self.style.profile)]

    def chunk(self, at, epoch, semantic_id, text, duration_ms):
        self._time(at)
        if self.summary_deadline is not None and at >= self.summary_deadline:
            return self.tick(at)
        if epoch != self.epoch or self.state not in {"main", "ack", "clarify", "summary"}:
            return [self._command("drop_stale", source_epoch=epoch)]
        if not semantic_id or duration_ms <= 0:
            raise ValueError("Chunk needs semantic identity and positive duration")
        if any(c.semantic_id == semantic_id for c in self.chunks[epoch]):
            return [self._command("drop_duplicate", semantic_id=semantic_id)]
        self.chunks[epoch].append(Chunk(semantic_id, text, duration_ms))
        return [self._command("enqueue", index=len(self.chunks[epoch])-1,
                              semantic_id=semantic_id, text=text)]

    def submitted_audio(self, at, epoch, index):
        self._time(at)
        if epoch == self.epoch and self.state in {"main", "ack", "clarify", "summary"}:
            if not 0 <= index < len(self.chunks.get(epoch, [])):
                raise ValueError("Unknown chunk submission")
            self.submitted.add((epoch, index))
        return []

    def _receipt(self, epoch, index, offset_ms):
        chunks = self.chunks.get(epoch, [])
        if index == -1 and offset_ms == 0 and self.played.get(epoch, (-1, 0)) == (-1, 0):
            return
        if not 0 <= index < len(chunks) or not 0 <= offset_ms <= chunks[index].duration_ms:
            raise ValueError("Invalid playback receipt")
        if (epoch, index) not in self.submitted:
            raise ValueError("Cannot render an unsubmitted chunk")
        if (index, offset_ms) < self.played.get(epoch, (-1, 0)):
            raise ValueError("Playback cursor regressed")
        self.played[epoch] = (index, offset_ms)
        if self.modes.get(epoch) == "main":
            c = chunks[index]
            self.cursor = dict(semantic_id=c.semantic_id, text=c.text,
                               played_ms=offset_ms, duration_ms=c.duration_ms,
                               completed=offset_ms == c.duration_ms)

    def receipt(self, at, epoch, index, offset_ms):
        self._time(at)
        if epoch != self.epoch or self.state not in {"main", "ack", "clarify", "summary"}:
            return []
        self._receipt(epoch, index, offset_ms)
        self.metrics.append(dict(event="played", at_ms=at, epoch=epoch))
        return []

    def overlap(self, at, echo="uncertain"):
        self._time(at)
        if echo not in {"echo_only", "near_end", "uncertain"}:
            raise ValueError("Invalid acoustic evidence")
        if echo == "echo_only":
            return [self._command("ignore_echo")]
        self.speaking_user = True
        if self.state == "stopping":
            return []
        self.classify_deadline = None
        self.decision = None
        self.summary_deadline = None
        self.metrics.append(dict(event="overlap", at_ms=at, echo=echo))
        if self.state in {"main", "ack", "clarify", "summary"}:
            if self.state == "main":
                self.topic_expires = at + self.style.topic_ttl_ms
            old = self.epoch
            self.pending_pause = old
            self.epoch += 1  # invalidate LLM/TTS output before issuing cancellation
            self.state = "paused"
            return [self._command("pause_flush", source_epoch=old),
                    self._command("cancel_generation", source_epoch=old)]
        self.epoch += 1  # invalidate any outstanding classifier result
        self.state = "paused"
        return []

    def pause_receipt(self, at, source_epoch, index, offset_ms):
        self._time(at)
        if source_epoch != self.pending_pause:
            return []
        self._receipt(source_epoch, index, offset_ms)
        self.pending_pause = None
        self.metrics.append(dict(event="playback_quiescent", at_ms=at, epoch=source_epoch))
        return self._resolve()

    def user_end(self, at, transcript):
        self._time(at)
        if not self.speaking_user:
            return []
        self.speaking_user = False
        self.transcript = transcript
        if self.state in {"listening", "stopping"}:  # e.g. stop already handled
            return []
        self.state = "classifying"
        self.classify_deadline = at + self.style.classify_timeout_ms
        return [self._command("classify", transcript=transcript, context=self.context,
                              played_cursor=self.cursor, profile=self.style.profile,
                              labels=["agreement", "assistance", "clarification", "disruption"])]

    def revise_transcript(self, at, revision, transcript, final=False):
        """Partial ASR cannot cause content actions. Revisions invalidate plans."""
        self._time(at)
        if revision <= self.asr_revision or self.state in {"listening", "stopping"}:
            return []
        self.asr_revision = revision
        cancellation = []
        if self.state in {"main", "ack", "clarify", "summary"}:
            cancellation = self.overlap(at, "uncertain")
            self.speaking_user = False  # revision of an already endpointed utterance
        self.epoch += 1
        self.decision = None
        self.transcript = transcript
        self.state = "paused"
        self.classify_deadline = None
        if not final or self.speaking_user:
            return cancellation
        self.speaking_user = True  # reuse endpointed final-transcript path
        return cancellation + self.user_end(at, transcript)

    def classified(self, at, epoch, intent, confidence):
        self._time(at)
        if epoch != self.epoch or self.state != "classifying":
            return []
        if self.classify_deadline is not None and at >= self.classify_deadline:
            return self._uncertain()
        if (intent not in {"agreement", "assistance", "clarification", "disruption"}
                or not isfinite(confidence) or confidence < self.style.confidence or confidence > 1):
            return self._uncertain()
        self.metrics.append(dict(event="intent_ready", at_ms=at, intent=intent))
        self.classify_deadline = None
        self.decision = intent
        return self._resolve()

    def _uncertain(self):
        self.classify_deadline = None
        self.decision = None
        self.state = "paused"
        return [self._command("listen", reason="uncertain_intent")]

    def _resolve(self):
        if self.pending_pause is not None or self.speaking_user or not self.decision:
            return []
        intent, self.decision = self.decision, None
        if intent == "disruption" and self.style.disruption == "yield":
            self.cursor = None
            self.context = ""
            self.state = "listening"
            return [self._command("yield")]
        self.intent = intent
        self.state = "planning"
        self.classify_deadline = self.now + self.style.classify_timeout_ms
        return [self._command("plan", intent=intent, profile=self.style.profile,
                              transcript=self.transcript, suspended_topic=self._topic())]

    def _topic(self):
        if self.topic_expires is None or self.now >= self.topic_expires:
            self.context = ""
            self.cursor = None
            return None
        return dict(context=self.context, cursor=self.cursor, expires_ms=self.topic_expires)

    def planned(self, at, epoch, action, content="", relevance=0.0, nod=False):
        """Semantic planner chooses content; category is evidence, not a script.

        resume explicitly regenerates from the heard boundary, never replays an
        old queue. revise/follow discard the suspended topic. All completions yield.
        """
        self._time(at)
        if epoch != self.epoch or self.state != "planning" or self.speaking_user:
            return []
        if self.classify_deadline is not None and at >= self.classify_deadline:
            return self._uncertain()
        self.classify_deadline = None
        if action not in {"ack", "clarify", "revise", "follow", "resume", "abandon", "summary"}:
            return self._uncertain()
        if action == "abandon":
            self.context = ""
            self.cursor = None
            self.state = "listening"
            return [self._command("yield")]
        if self.intent == "disruption" and action != "summary":
            return self._uncertain()  # disruption may only summarize briefly or yield
        if action == "summary" and (self.intent != "disruption" or self.style.disruption != "summary"):
            return self._uncertain()
        topic = self._topic()
        if action == "resume" and (not topic or not isfinite(relevance) or not 0.5 <= relevance <= 1):
            return self._uncertain()
        if action in {"revise", "follow"}:
            self.context = content
            self.cursor = None
            self.topic_expires = None
        self._stage(action if action in {"ack", "clarify", "summary"} else "main")
        if action == "summary":
            self.summary_deadline = self.now + self.style.summary_ms
        return [self._command("resume" if action == "resume" else "respond",
                              action=action, content=content, profile=self.style.profile,
                              nod=bool(nod), suspended_topic=topic if action not in {"revise", "follow"} else None,
                              max_audio_ms=self.style.summary_ms if action == "summary" else 1500 if action == "ack" else None)]

    def finished(self, at, epoch):
        """Only after output device confirms ALL audio played; not LLM/TTS done."""
        self._time(at)
        if epoch != self.epoch or self.speaking_user or self.pending_pause is not None:
            return []
        chunks = self.chunks.get(epoch, [])
        if chunks and self.played.get(epoch) != (len(chunks)-1, chunks[-1].duration_ms):
            return []  # generation/queue completion is not audible completion
        if self.state in {"ack", "clarify"}:
            self.epoch += 1
            self.state = "planning"
            self.classify_deadline = at + self.style.classify_timeout_ms
            return [self._command("plan", phase="after_response", intent=self.intent,
                                  profile=self.style.profile, suspended_topic=self._topic())]
        if self.state in {"summary", "main"}:
            self.summary_deadline = None
            self.cursor = None
            self.context = ""
            self.state = "listening"
            return [self._command("yield")]
        return []

    def stop(self, at):
        """Trusted explicit stop/cancel event bypasses classifier and personality."""
        self._time(at)
        old = self.epoch
        self.epoch += 1
        self.state = "stopping"
        self.cursor = None
        self.context = ""
        self.pending_pause = self.decision = None
        self.classify_deadline = self.summary_deadline = None
        return [self._command("stop_flush_all"), self._command("cancel_generation", source_epoch=old)]

    def stopped(self, at, epoch):
        self._time(at)
        if epoch == self.epoch and self.state == "stopping":
            self.state = "listening"
            self.metrics.append(dict(event="stop_quiescent", at_ms=at, epoch=epoch))
        return []

    def tick(self, at):
        self._time(at)
        if self.summary_deadline is not None and at >= self.summary_deadline:
            return self.stop(at) + [self._command("yield", reason="summary_deadline")]
        if self.classify_deadline is not None and at >= self.classify_deadline:
            return self._uncertain()
        return []
