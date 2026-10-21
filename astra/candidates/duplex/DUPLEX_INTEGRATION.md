# Isolated conversational turn policy

`duplex_controller.py` is a deterministic event-to-command policy. `duplex_adapter.py` provides a serialized, session-scoped passive boundary whose default sink records commands in memory. Microphone and camera flags start false; the package has no device-enabling API.

A host must supply monotonic integer milliseconds and serialize events. Acoustic near-end or uncertain overlap pauses before semantic classification. Explicit stop bypasses personality and classifier policy. Cancellation invalidates old epochs; actual device adapters must atomically recheck epochs at output admission, including after cancellation.

Generated and submitted chunks are not evidence of heard speech. Report cumulative actual render receipts, and a final pause receipt only after playback is silent. Planning waits for that receipt. Never use a timeout to assume silence. Resume requires an explicit relevant plan and unexpired context; acknowledgment or clarification does not resume automatically. ASR revisions invalidate prior decisions. Uncertain intent stays quiet.

Host sinks must return promptly. Prioritize stop and overlap over slow callbacks; enforce response budgets in the device as well as the policy timer. Echo cancellation, VAD, ASR, intent classification, semantic planning, generation, TTS, playback and animation adapters are not implemented. The core consumes acoustic evidence; it does not establish its correctness.

## ASR identity correction (pending independent re-review)

Independent review found that stale ASR corrections could affect a new response, and that the revision counter was not scoped to an utterance. The corrected candidate requires `utterance_id` on both `user_end` and `revise_transcript`. `TurnSession.asr_onset` atomically handles onset and captures session/utterance identity before an ASR job starts. Keep that captured identity on every callback; never relabel delayed results with the current identity. Session IDs must be unique across controller lifetimes.

Revisions are monotonic within an utterance and restart for a new utterance. Stop and a fresh assistant `begin` retire the previous identity; a newer human utterance supersedes it. Valid corrections retain their identity across output epoch changes and response cancellation. Repeated acoustic activity during the same utterance retains its identity.

23 synthetic tests passed in the corrected publication copy (the original 18 plus five regressions for stale corrections, revision restart, stale endpoints, valid correction identity and adapter propagation). Independent re-review is pending. No microphone, speaker, model or live app was activated, and no hardware latency was measured. A future audio pilot needs separate integration review and explicit authorization.
