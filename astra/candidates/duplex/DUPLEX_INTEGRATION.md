# Isolated conversational turn policy

`duplex_controller.py` is a deterministic event-to-command policy. `duplex_adapter.py` provides a serialized, session-scoped passive boundary whose default sink records commands in memory. Microphone and camera flags start false; the package has no device-enabling API.

A host must supply monotonic integer milliseconds and serialize events. Acoustic near-end or uncertain overlap pauses before semantic classification. Explicit stop bypasses personality and classifier policy. Cancellation invalidates old epochs; actual device adapters must atomically recheck epochs at output admission, including after cancellation.

Generated and submitted chunks are not evidence of heard speech. Report cumulative actual render receipts, and a final pause receipt only after playback is silent. Planning waits for that receipt. Never use a timeout to assume silence. Resume requires an explicit relevant plan and unexpired context; acknowledgment or clarification does not resume automatically. ASR revisions invalidate prior decisions. Uncertain intent stays quiet.

Host sinks must return promptly. Prioritize stop and overlap over slow callbacks; enforce response budgets in the device as well as the policy timer. Echo cancellation, VAD, ASR, intent classification, semantic planning, generation, TTS, playback and animation adapters are not implemented. The core consumes acoustic evidence; it does not establish its correctness.

18 synthetic tests passed in the publication copy. No microphone, speaker, model or live app was activated, and no hardware latency was measured. A future audio pilot needs separate integration review and explicit authorization.
