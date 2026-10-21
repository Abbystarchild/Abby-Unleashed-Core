# Astra progress snapshot

This is a review snapshot, not a completed release or a replacement for the legacy application. The repository's existing MIT license and authorship remain unchanged. All additions are isolated under `astra/`; existing launch paths are unchanged.

## Feature status

| Area | Status and evidence boundary |
| --- | --- |
| Qwen3-4B identity correction and plain personal chat | Reported deployed by the local runtime owner. This publication task did not run or independently requalify the live model. The personal runtime, profiles, and deployment configuration are deliberately not packaged here. |
| Foundation | Offline source slice: bounded scoped memory, provider contracts, explicit read capability, hash-checked reads and outcome journaling. Generated prose remains `needs-review`. Direct HTTP transport is disabled by default. Synthetic tests only in this snapshot. |
| Conversational turn controller | Isolated tested candidate with an ASR utterance-identity correction; independent re-review pending. Acoustic overlap, cancellation epochs, rendered-position receipts, transcript revisions, planning boundaries and stop behavior are policy events. No live audio integration or latency achievement. |
| Personality calibration | Isolated tested candidate with neutral defaults, explicit reviewed examples, versioned preferences, undo/reset/export and an offline editor. This is prompt calibration, not fine-tuned weights. No adoption by live personal chat. |
| Integration and release readiness | Unreviewed for production. Device adapters, live integration and model evaluation remain pending. |
| Future work | Live duplex pilot, echo cancellation, streaming ASR/TTS, personal-style evaluation, any weight training, and dreaming remain planned, not delivered by this snapshot. |

## Offline validation

From the repository root, using an existing Python 3.14 interpreter:

```text
python -S -B -m unittest discover -s astra/foundation -p test_astra.py -v
python -S -B -m unittest discover -s astra/candidates/duplex -p test_duplex_controller.py -v
python -S -B -m unittest discover -s astra/candidates/personality -p test_personality.py -v
```

The initial publication copy passed 17 foundation, 18 duplex and 13 personality tests (48 total). The duplex correction passed 23 tests (original 18 plus five regressions); foundation and personality results remain from the initial publication and were not rerun for this duplex-only follow-up. Independent re-review of the duplex correction is pending. Tests use synthetic inputs, mocks and disposable databases; they do not call models or activate devices. The foundation compatibility test extracts only the repository client's `chat` method and uses a mocked HTTP interface; it does not import or start the legacy application. Its source pin uses normalized line endings.

The personality owner separately reported 29 automated local Tk checks; those were not rerun for publication. Subjective visual acceptance, other display scales and actual model behavior are not established by these unit tests. The editor is included as source and was not opened in this task.

## Publication boundaries

Only the listed source files, synthetic tests, documentation and content hashes are included. No model weights, real profiles/examples, correspondence, conversations, logs, recordings, images, credentials, machine configuration or runtime databases are added. Synthetic participant labels are generalized. The foundation's original absolute compatibility-test path is made repository-relative. Original local sources were not modified.

The stable personality input manifest was verified as SHA-256 `c8356fb2183e8c7b3761fe1d0229eec9ae3dca4cf829db3fddd906a4f20bc849` before copying its four source/test files. `FILES.sha256` records the publication copy, including sanitization changes. No user calibration data is included.

This review does not certify or alter historical repository contents. Existing files, history and license are retained.
