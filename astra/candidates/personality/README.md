# Isolated personality calibration

The store begins at neutral traits and zero examples. Users explicitly author and review relevant style feedback. Six traits, scoped examples, append-only revisions, optimistic version checks, undo/reset, local export and expiring process-local mood are implemented. Factual corrections and rejected wording are excluded from style retrieval.

`prepare_messages` is a future adapter hook. It preserves existing messages, appends fixed style rules, and inserts bounded quoted preference data. It fails on capacity overflow rather than truncating history. Serialization tests do not guarantee a model will respect these boundaries.

`editor.py` is an optional local Tk editor that creates a dedicated calibration database beside itself when explicitly run. Its preview shows context only, not generated responses. Do not commit that database or exported preferences. This snapshot does not launch it or integrate it into live chat.

13 synthetic unit tests passed in the publication copy. The owner separately reported 29 automated UI checks on the stable candidate, not independent production acceptance. No model training, live response comparison, private examples, biography or learned weights are included.
