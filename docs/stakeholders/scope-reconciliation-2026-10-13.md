# Scope website reconciliation — October 13, 2026

The leadership scope page retained repeated open questions and old week-based
assignments despite the August stakeholder response. The update preserves
scope-history.html and its hash routes, adds answered-evidence sections and
remaining follow-ups to all eleven sections, and separates policy guidance from
implementation proof. The original page is preserved at
history/scope-design-2026-08.html.

Source: stakeholders/answers-2026-08.md, including its distinction between
Joanne's responses and the author's engineering interpretation. Current
implementation evidence is drawn from PROJECT-GUIDE.md and source-inspected code.

| Area | Recorded answer | Remaining follow-up |
| --- | --- | --- |
| Upstream handoff | Tracy performs preservation processing; appraisal review is the bottleneck (§1.2) | Output format/tools, approved read access and inventory |
| Identity | Record-series numbers, human assignment; unnumbered formal accessions set aside (§2) | Delivery/file identity tests and upstream mapping |
| Appraisal | Personal-paper/administrative guidance and expertise route (§3) | Complete criteria, independent labels, acceptance thresholds |
| Software | BitCurator yes; Preservica/Archivematica no; DROID uncertain; ePADD trial (§4) | DROID/output confirmation; ePADD IT permission |
| Metadata | Existing collection-level descriptions; label generated fields (§5.2–5.3) | Concrete crosswalk and item/folder linking contract |
| Review/disposition | Supervising archivist for sensitive flags, accessioning archivist for disposal; endorsed starting oversight (§6) | Capacity, implemented sampling/disposition and operational interval |
| Restrictions | Open/restricted; point-in-time no holds; intended unredacted access (§7) | Restriction references, vault controls, NDA process and provisioned access |
| Scheduling | August backlog and turnaround targets (§1.4/8.2) | Current counts/bytes, priorities and measured capacity |

Removed unsupported performance guarantees and the calculator that transferred
POC timings to the unmeasured current workload. A reported 150,000-file scenario
is explicitly not an inventory. No autonomous deletion, implemented retention
clock, complete format support, Gauri API access or archival accuracy is claimed.
The diagram is labelled as scope handoffs, and the displayed date is the content
review date rather than today's browser date. Roles match Tayler integration and
Gauri evaluation/performance ownership.

Validation: inline JavaScript compilation; all eleven sections checked for
answered/follow-up data; browser preview of inventory, governance, metadata and
home; historical hash route IDs retained; git diff --check. No live website
publication or model/server changes are performed by preparing this PR.
