# Accession context and model use

`src/context.py` constructs selected accession context with provenance. Its allowed context fields include source, owner, role, scope, research and biography. Valuable and excluded material is withheld from general description context. The sensitivity-only mode is a helper capability; each caller must be checked before assuming it uses that mode.

Sensitivity and deterministic institutional rules take precedence over content relevance and proximity. Context is supporting evidence, not permission to override policy. Association must be explicit where required. Model-generated metadata needs factual review in addition to schema validation, and missing evidence must not become invented dates, creators or relationships.

Required pseudonymized text must fail closed when unavailable; the relevant pipeline repair is proposed in PR #79. Hosted validation uses synthetic fixtures only. Frontier judging is a later funded step and does not authorize sending real records to external models.

See the [pipeline design](design/pipeline-design.md), [validation grading](../validation/GRADING.md) and [historical rationale](history/docs/ai-and-the-accession-form.md). A context hash or version records provenance, not human approval.
