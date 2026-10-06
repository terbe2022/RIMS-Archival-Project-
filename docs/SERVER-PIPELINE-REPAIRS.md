# Pipeline repairs — 6 October 2026

These changes repair repository source corresponding to the selected server
source snapshot. They have been tested locally with synthetic inputs. They
have not been deployed to AITS or verified against running services.

## Changed behavior

- Direct script execution resolves `src/workbench` and the shared schema.
  A compatibility package keeps the live `workbench.schema` import spelling.
- The vision prompt loads and its example is valid JSON with an evidence field.
- Text descriptions require pseudonymized input by default. Missing or empty
  per-file text fails without a model call; absence is not evidence of safety.
  `--allow-raw` remains an explicit operator option for separately authorized
  inputs, including synthetic tests; it grants no data-policy exception.
- Lane orchestration checks text input directories before starting any models
  and returns failure when a child lane fails.
- Schema 1.2 persists nullable association-retention evidence. See the schema
  changelog; older manifests remain readable.
- Single-process decision writes read their predecessor under the same lock
  as append, carry unique event IDs, and flush/fsync. Legacy predecessors use
  their timestamps. Corrupt history blocks new writes rather than being ignored.
- The default decision log is outside the static payload root. If a legacy
  in-root log exists, startup requires an explicit `--log` selection so existing
  history is not abandoned. Static/encoded log URLs and containing directory
  listings are denied; API retrieval remains available.
- Public demo exporters use generated identities, typed numeric/boolean values,
  and fixed enums. They omit policy prose, rationales, unknown fields and source
  identifiers. Public prototype counts are recomputed from selected records.
- Sync requires individually selected `--include-doc NAME.md` documents, refuses
  `--force`, validates public sanitization in temporary storage during dry runs,
  and returns failure for blocked files or a failed public build.

## Validation

Run `python -B -m unittest discover -s tests -v` with pandas, pyarrow and requests.
The regression suite covers script imports, source parsing, prompt JSON,
manifest round-trip, missing pseudonymized inputs, concurrent HTTP decision
writes, static log protection, corrupt history, closed public export allow-lists,
and sync dry-run behavior. Existing schema rules behavioral checks also pass.
No model calls, real accession processing, or remote server commands were run.

## Remaining operational work

The decision server still has no authenticated identity or cross-process
transaction store. These repairs do not make it a production multi-user service.
Keep it behind approved access controls. Back up existing decision history before
an authorized deployment; retain the log format and explicit path selection.

Stored reviewed release artifacts, destination contracts, UI Publish/export
integration and export/re-ingest acceptance remain separate engineering work.
The selected source did not establish the allegedly `--thumbs`-enabled exporter
or the actual server UI version. Public transformation is not publication
approval, and counts/metadata still require authorized source selection.
