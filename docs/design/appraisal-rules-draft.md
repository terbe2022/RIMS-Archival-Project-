# Appraisal rules — draft for confirmation

**Drafted 13 August 2026 by Tayler Erbe, from the University Archives' answers to questions
3.2 and 3.3.** Policy version `0.1-draft`.

This is our reading of what you told us, written out in plain language so you can correct it.
Nothing here is settled. Where we inferred something rather than being told it, it says so.

## How to read this

Every file gets checked against three sets of rules, in this order:

1. **Sensitive** — if any of these match, the file goes to a supervising archivist and nothing
   else applies. It is never discarded automatically.
2. **Keep** — first match wins.
3. **Set aside** — first match wins. Only reached if nothing above matched.

A file matching no rule at all is **not** discarded. It is marked as *no rule had an opinion*
and stays available for review.

## The one change we made on your behalf

In answer 3.3 you listed HR material — FMLA details, discipline matters, internal personnel
discussions — as routinely safe to set aside, and noted in the same sentence that it is
sensitive content.

We have treated those as **two different outcomes rather than one**. Anything reading as a
personnel matter routes to a supervising archivist for review, even when a disposal rule also
matches it. Our reasoning: discarding personnel records nobody has read is not a recoverable
mistake, and over-routing to review is.

That is a decision we made without asking, and you should have the chance to disagree with it.

---

# personal_papers

Personal papers of faculty and alumni. Drafted from the University Archives' answers to questions 3.2 and 3.3, August 2026. Correspondence is the highest-value category. Turnaround target is 3–6 months from receipt (answer 8.2), so there is no reason to prefer speed over care.

Policy version `0.1-draft` — **draft, not yet confirmed**.

## Always flagged for a supervising archivist

These are never discarded automatically, whatever else matches them.

**pp.sensitive.personal_finance**

Personal financial material. The Archives lists this as normally disposable, but it carries personal information, so a person decides rather than a rule.

*Source: Answer 3.3, plus PII precedence*

> Joanne listed personal finance under 'set aside'. We route it to review rather than disposal because discarding unread financial records is not recoverable. Worth confirming she is happy with that.

**pp.sensitive.medical**

Medical or health-related material. Always reviewed by a person.

*Source: Standing sensitivity policy, not from 3.3*

**pp.sensitive.student_records**

Possible student records, which are FERPA-covered. Reviewed by a supervising archivist before any disposition.

*Source: FERPA obligation; not raised in 3.3 but unavoidable in faculty material*

> A faculty drive will contain grading material. This rule is broad on purpose — over-routing to review is recoverable.

## Kept

Matched in this order; the first match wins.

**pp.retain.correspondence**

Correspondence. The Archives names this first among material always worth keeping, particularly where it touches research, committees, teaching or publications.

*Source: Answer 3.2*

> Deliberately broad. Answer 1.7 confirms .eml and .pst arrive inside personal papers accessions, so this rule is also what routes email into the main line rather than a separate phase.

**pp.retain.grants**

Grant applications and grant reports. Named explicitly as always kept.

*Source: Answer 3.2*

**pp.retain.publications**

Articles and books the person wrote. Named as always kept.

*Source: Answer 3.2*

**pp.retain.committees_and_service**

Participation on committees and boards. Named as always kept.

*Source: Answer 3.2*

**pp.retain.teaching**

Material about courses taught. Named as always kept.

*Source: Answer 3.2*

> Distinct from grading material, which is sensitive — the sensitivity rules run first, so a gradebook inside a teaching folder still routes to review.

**pp.retain.research**  *(tentative — please check)*

Research material. Answer 3.2 treats research as the thing that makes other categories valuable, so it is retained in its own right.

*Source: Answer 3.2, inferred*

> Inferred rather than stated. Joanne named correspondence *referencing* research; she did not explicitly say research files themselves. Please confirm.

**pp.retain.drafts_humanities**

Drafts of published work, for a humanities scholar. The Archives singles these out as valuable for this group specifically.

*Source: Answer 3.2 — 'for some faculty, humanities scholars, English professors for example, the drafts of their final published works would be valuable to keep'*

> This is why the accession profile matters. The same file is kept for an English professor and set aside for a chemist. `profile_field` on the accession record selects which applies. If it is missing, this rule cannot fire and the file falls through to review.

## Set aside

Proposed for disposal, subject to sampling and the retention clock. Never applied to anything above.

**pp.discard.system_files**

Operating system or application file, not a record the person created.

*Source: Answer 3.3 — 'everything related to the system operations'*

**pp.discard.installed_software**  *(tentative — please check)*

Software the person installed on their own machine.

*Source: Answer 3.3 — 'MOST software applications that the person may have loaded onto their computer'*

> Joanne said MOST, not all. If a researcher wrote or heavily customised software, that is scholarly output and this rule would be wrong. Sampled harder because of the hedge.

**pp.discard.commercial_entertainment**

Commercial entertainment the person loaded themselves.

*Source: Answer 3.3 — 'personally loaded up commercial entertainment'*

> Deliberately does not include .mp4 or .mov. Both are in the Archives' confirmed format list (answer 1.7) and are as likely to be recorded lectures or fieldwork as entertainment. Folder context decides those.

**pp.discard.browser_artifacts**

Browser artefacts. System operations material rather than a record.

*Source: Answer 3.3, inferred from 'system operations'*

## Anything else

A file matching no rule is **not** discarded. It is marked `not_selected`, which means no rule had an opinion about it, and it stays available for review.


---

# administrative

Administrative records from university offices — Chancellor's Files, President's Office, deans and directors. Drafted from the University Archives' answers to questions 3.2 and 3.3, August 2026. Turnaround target is no more than 3 months (answer 8.2), tighter than personal papers.

Policy version `0.1-draft` — **draft, not yet confirmed**.

## Always flagged for a supervising archivist

These are never discarded automatically, whatever else matches them.

**admin.sensitive.personnel**

Personnel or disciplinary matter. The Archives lists this as normally disposable AND marks it sensitive. It is never discarded on a rule match — a supervising archivist decides.

*Source: Answer 3.3 — 'HR related info such as FMLA details, discipline matters, internal personnel discussions (sensitive content)'*

> This is the rule the four-value decision enum exists for. If discard and sensitive were one disposition, this material could be binned without anyone reading it. Flagging to Joanne that we made this distinction on her behalf.

**admin.sensitive.fmla_medical**

Medical leave or accommodation material, named explicitly as sensitive.

*Source: Answer 3.3*

**admin.sensitive.student_records**

Possible student records, FERPA-covered.

*Source: FERPA obligation; not from 3.3 but unavoidable in office records*

**admin.sensitive.legal**  *(tentative — please check)*

Possible legal or privileged material.

*Source: Standing policy*

> Not raised in the answers. Included because university office records routinely contain it and the cost of getting it wrong is high. Answer 7.2 confirms nothing is currently under litigation hold.

## Kept

Matched in this order; the first match wins.

**admin.retain.leadership_communications**

Dean or Director communications. Named first among material always kept from university offices.

*Source: Answer 3.2*

**admin.retain.annual_reports**

Annual reports from the office. Named as always kept.

*Source: Answer 3.2*

**admin.retain.task_force_reports**

Task force reports. Named as always kept.

*Source: Answer 3.2*

**admin.retain.minutes_and_agendas**

Meeting minutes and agendas for college or school faculty meetings. Named as always kept.

*Source: Answer 3.2*

**admin.retain.annual_budgets**

Annual budgets. Named as always kept — as distinct from the transaction-level accounting detail listed as disposable.

*Source: Answer 3.2 (keep) read against 3.3 (discard)*

> The line here is between a budget as a planning document and the accounting exhaust of executing it. Joanne keeps the first and discards the second. This rule tries to encode that and is the one most likely to need correcting.

**admin.retain.enrollment_statistics**

Statistics on enrollment. Named as always kept.

*Source: Answer 3.2*

> Aggregate statistics only. Individual student records route to restricted review via admin.sensitive.student_records, which runs first.

**admin.retain.curriculum_changes**

Proposed changes to curricula, courses and goals — drafts as well as final versions. Named as always kept, explicitly including drafts.

*Source: Answer 3.2 — 'drafts and final versions of proposed changes to curricula, to courses, to goals, etc.'*

> Note the contrast with personal papers, where drafts are kept only for humanities scholars. Here they are kept unconditionally, because a rejected proposal is evidence of what the college considered.

## Set aside

Proposed for disposal, subject to sampling and the retention clock. Never applied to anything above.

**admin.discard.accounting_detail**

Transaction-level accounting detail — purchases and expenditures. Named as safe to set aside.

*Source: Answer 3.3 — 'accounting details related to general oversight of budget expenditures such as purchases'*

> Deliberately narrower than 'anything financial'. Annual budgets are kept; the purchase orders that execute them are not.

**admin.discard.payroll_and_timesheets**

Payroll records and timesheets. Named as safe to set aside.

*Source: Answer 3.3*

> Sensitivity rules run first, so anything that also reads as a personnel matter routes to review instead. Salary data on named individuals is the case to watch — worth asking Joanne whether this rule should be narrower.

**admin.discard.system_files**  *(tentative — please check)*

Operating system or application file, not an office record.

*Source: Answer 3.3, read across from the personal papers guidance*

> Joanne listed system files under personal papers rather than administrative records. Applied here too because office drives carry the same junk, but it is an extension of what she said rather than what she said.

## Anything else

A file matching no rule is **not** discarded. It is marked `not_selected`, which means no rule had an opinion about it, and it stays available for review.


---

## What we would like from you

Not a full review. Three things would be enough:

1. **Anything marked *(tentative — please check)*.** Those are rules we inferred rather than
   ones you stated. Six of them.
2. **The two rules we are least sure of.** `admin.retain.annual_budgets` tries to separate a
   budget as a planning document from the purchase orders that execute it — we keep the first
   and set aside the second. And `admin.discard.payroll_and_timesheets`, where salary data on
   named individuals may need to be narrower.
3. **Anything obviously missing.** A category the Archives always keeps that we have not
   captured is a more useful correction than a rule that is slightly too broad.

The 50-file labelled sample would then tell us whether our reading matches yours in practice,
which is a smaller ask than the 300–500 files we originally proposed.
