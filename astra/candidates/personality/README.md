# Isolated personality calibration

The store begins at neutral traits and zero examples. Users explicitly author and review relevant style feedback. Six traits, scoped examples, append-only revisions, optimistic version checks, undo/reset, local export and expiring process-local mood are implemented. Factual corrections and rejected wording are excluded from style retrieval.

`prepare_messages` is a future adapter hook. It preserves existing messages, appends fixed style rules, and inserts bounded quoted preference data. It fails on capacity overflow rather than truncating history. Serialization tests do not guarantee a model will respect these boundaries.

`editor.py` is an optional local Tk editor that creates a dedicated calibration database beside itself when explicitly run. Its preview shows context only, not generated responses. Do not commit that database or exported preferences. This snapshot does not launch it or integrate it into live chat.

## Draft protection correction (v2; independent re-review pending)

Undo and Reload now ask before discarding unsaved traits or examples, with No as the default. Reset confirms draft discard separately from resetting saved preferences; cancelling either preserves the draft. Reset wording clarifies that Undo restores saved versions, not discarded unsaved edits. Reload recovers the latest saved version after a conflict, with dirty detection relative to the editor's loaded snapshot. Malformed JSON drafts remain protected.

The source manifest for v2 was verified as SHA-256 `df6e046efdec32fbac4bc451126be332cc047eb6226bd53709c84c76c6dcabfb`. Only `editor.py` changes application behavior; the data model, baseline and unit tests are unchanged from the preceding source version. The publication copy generalizes its synthetic participant label. No local user calibration was read or copied.

The corrected publication copy passed 13 unit tests, 15 focused checks in `check_draft_protection.py` for draft cancellation, malformed drafts, stale saves and reload recovery, and 31 automated Tk interaction/geometry checks in `check_editor.py`. Both UI checks use disposable test databases and automated dialogs; run explicitly with an existing Python/Tk installation. They create test-owned windows and local result JSON, not live app sessions. Independent re-review and subjective visual acceptance remain pending. No model training, live response comparison, private examples, biography or learned weights are included.
