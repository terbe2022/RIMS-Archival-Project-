# Manifest contract

The executable contract is [src/schema/manifest.py](../../src/schema/manifest.py). Main's baseline is v1.1. [PR #79](https://github.com/terbe2022/RIMS-Archival-Project-/pull/79) proposes v1.2 with nullable association so that unknown evidence is not converted to false. Use the schema from the exact commit being tested.

The manifest connects inventory identity and source provenance with appraisal, sensitivity, extraction and description records. A file identity derived from accession and path is stable for that path, not a guarantee that moving a file preserves its identifier. Optional or unknown values must retain the contract's explicit missing-value representation.

Fields representing retention, access or review state do not prove that a disposal scheduler, policy approval or release workflow exists. Machine-produced description is not accepted archival description. Inspect the executable validators for required keys, enums and type constraints; do not substitute historical prose for those checks.

Association, disposition and access have separate meanings. In particular, lack of association evidence is not a negative decision. Resolve policy uncertainty through the [decision register](../DECISIONS.md) and authorized institutional owners.

The [preserved v1.1 specification](../history/docs/design/manifest-schema.md) and [schema changelog](schema-changelog.md) provide supporting history. Historical automation claims require separate implementation and acceptance evidence.
