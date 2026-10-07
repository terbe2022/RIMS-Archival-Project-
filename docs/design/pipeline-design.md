# Current pipeline design

Source-oriented description reviewed October 7, 2026. The [earlier design](../history/docs/design/pipeline-design.md) preserves architectural rationale and proposed features; it is not the operating specification.

| Layer | Current purpose | Verification boundary |
| --- | --- | --- |
| Inventory and identity | Describe upstream files and stable manifest identities. | Source exists; coverage across real collections is not established here. |
| Appraisal and sensitivity | Apply rules and record reviewable decisions. | Policy ratification is separate from implementation. No autonomous disposal. |
| Extraction | Route supported file types to extraction paths. | Unsupported or failed extraction must remain visible; historical POC coverage is not current acceptance. |
| Model description | Generate metadata using selected context and permitted inputs. | Schema checks are not factual validation. Required pseudonymization repairs are in PR #79. |
| Manifest | Carry provenance, classification and description fields. | Main baseline v1.1; v1.2 association change is pending PR #79. |
| Human review | Present records and capture decisions in the prototype workbench. | Authentication, operational configuration and server acceptance remain outstanding. |
| Export | Prepare selected metadata for downstream use. | A generated payload is not an approved release or completed repository integration. |

Sensitivity outranks appraisal rules, content signals and proximity. Explicit association evidence must not be replaced by inferred relatedness. Valuable or excluded context is withheld from general description prompts. Model output remains unreviewed until human acceptance.

Read the [manifest contract](manifest-schema.md), [context guidance](../ai-and-the-accession-form.md), [institutional questions](../stakeholders/open-questions.md) and [engineering handoff](../HANDOFF.md) for constraints. Published source repairs do not establish that the live server uses them.
