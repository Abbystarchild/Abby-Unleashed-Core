# Astra progress snapshot

This is a review snapshot, not a completed release or a replacement for the legacy application. The repository's existing MIT license and authorship remain unchanged. All additions are isolated under `astra/`; existing launch paths are unchanged.

## Feature status

| Area | Status and evidence boundary |
| --- | --- |
| Qwen3-4B identity correction and plain personal chat | Reported deployed by the local runtime owner. This publication task did not run or independently requalify the live model. The personal runtime, profiles, and deployment configuration are deliberately not packaged here. |
| Foundation | Offline source slice: bounded scoped memory, provider contracts, explicit read capability, hash-checked reads and outcome journaling. Generated prose remains `needs-review`. Direct HTTP transport is disabled by default. Synthetic tests only in this snapshot. |
| Conversational turn controller | Isolated tested candidate with an ASR utterance-identity correction; independent re-review pending. Acoustic overlap, cancellation epochs, rendered-position receipts, transcript revisions, planning boundaries and stop behavior are policy events. No live audio integration or latency achievement. |
| Personality calibration | Isolated candidate with neutral defaults, explicit reviewed examples, versioned preferences and an offline editor. The v2 correction protects drafts during Undo/Reset/Reload and recovers stale versions; independent re-review pending. This is prompt calibration, not fine-tuned weights. No adoption by live personal chat. |
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

The personality-v2 follow-up reruns the 13 data-model tests and the 15 focused draft-protection plus 31 Tk interaction/geometry checks on disposable synthetic profiles. Test-owned editor windows are separate from live calibration. Independent re-review, subjective visual acceptance, other display scales and actual model behavior are not established by these checks.

## Publication boundaries

Only the listed source files, synthetic tests, documentation and content hashes are included. No model weights, real profiles/examples, correspondence, conversations, logs, recordings, images, credentials, machine configuration or runtime databases are added. Synthetic participant labels are generalized. The foundation's original absolute compatibility-test path is made repository-relative. Original local sources were not modified.

The initial personality-v1 manifest was verified as SHA-256 `c8356fb2183e8c7b3761fe1d0229eec9ae3dca4cf829db3fddd906a4f20bc849`. The corrected personality-v2 manifest was verified as `df6e046efdec32fbac4bc451126be332cc047eb6226bd53709c84c76c6dcabfb` before copying its corrected editor and synthetic checks. `FILES.sha256` records the publication copy, including sanitization changes. No user calibration data is included.

This review does not certify or alter historical repository contents. Existing files, history and license are retained.
