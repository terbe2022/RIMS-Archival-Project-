"""
rules/administrative.py

Drafted from the University Archives' answers of 12 Aug 2026, questions 3.2 and
3.3. **Not confirmed.**

Their words, 3.2 — always keep:

    For administrative records from university offices: Dean or Director
    communications, annual reports from the office, task force reports, meeting
    minutes and agendas for college or school faculty meetings, annual budgets,
    stats on enrollment, drafts and final versions of proposed changes to
    curricula, to courses, to goals, etc.

Their words, 3.3 — nearly always set aside:

    For administrative records from university offices: Accounting details
    related to general oversight of budget expenditures such as purchases,
    payroll records, timesheets. HR related info such as FMLA details,
    discipline matters, internal personnel discussions (sensitive content).

Two things to notice, both of which shaped this file.

First, **drafts are kept here and conditional in personal papers.** Answer 3.2
says "drafts and final versions of proposed changes to curricula" without
qualification. A rejected curriculum proposal is evidence of what the college
considered, so the draft carries information the final version does not.

Second, **the HR sentence ends with "(sensitive content)".** Joanne listed HR
material as disposable and then flagged it as sensitive in the same breath.
Those are different dispositions and this file does not collapse them.
"""
from .base import (Rule, Ruleset, ext, path_contains, folder_named,
                   filename_matches, text_mentions, any_of, all_of, not_)

# ═══════════════════════════════════════════════════════════════ sensitive ══
# The whole reason s02_decision has four values rather than two.

SENSITIVE = [
    Rule(
        name="admin.sensitive.personnel",
        disposition="restricted_review",
        match=any_of(
            folder_named("hr", "human resources", "personnel", "discipline",
                         "grievance", "grievances", "complaints"),
            path_contains("/personnel", "/hr/", "disciplinary", "grievance",
                          "performance review", "termination", "misconduct"),
            text_mentions("disciplinary", "grievance", "performance improvement",
                          "misconduct", "termination"),
        ),
        because="Personnel or disciplinary matter. The Archives lists this as normally "
                "disposable AND marks it sensitive. It is never discarded on a rule "
                "match — a supervising archivist decides.",
        source="Answer 3.3 — 'HR related info such as FMLA details, discipline "
               "matters, internal personnel discussions (sensitive content)'",
        notes="This is the rule the four-value decision enum exists for. If discard "
              "and sensitive were one disposition, this material could be binned "
              "without anyone reading it. Flagging to Joanne that we made this "
              "distinction on her behalf.",
    ),
    Rule(
        name="admin.sensitive.fmla_medical",
        disposition="restricted_review",
        match=any_of(
            path_contains("fmla", "medical leave", "ada accommodation",
                          "workers comp", "disability"),
            text_mentions("FMLA", "medical leave", "accommodation request"),
        ),
        because="Medical leave or accommodation material, named explicitly as "
                "sensitive.",
        source="Answer 3.3",
    ),
    Rule(
        name="admin.sensitive.student_records",
        disposition="restricted_review",
        match=any_of(
            folder_named("students", "admissions", "grades", "transcripts",
                         "financial aid"),
            path_contains("transcript", "student record", "admission file"),
            text_mentions("FERPA", "student record"),
        ),
        because="Possible student records, FERPA-covered.",
        source="FERPA obligation; not from 3.3 but unavoidable in office records",
    ),
    Rule(
        name="admin.sensitive.legal",
        disposition="restricted_review",
        match=any_of(
            folder_named("legal", "litigation", "counsel", "settlements"),
            path_contains("attorney", "privileged", "settlement agreement",
                          "legal counsel"),
            text_mentions("attorney-client", "privileged and confidential"),
        ),
        because="Possible legal or privileged material.",
        source="Standing policy",
        confidence="tentative",
        notes="Not raised in the answers. Included because university office records "
              "routinely contain it and the cost of getting it wrong is high. "
              "Answer 7.2 confirms nothing is currently under litigation hold.",
    ),
]

# ══════════════════════════════════════════════════════════════════ retain ══

RETAIN = [
    Rule(
        name="admin.retain.leadership_communications",
        disposition="selected",
        match=any_of(
            folder_named("dean", "director", "chancellor", "provost", "president"),
            path_contains("/dean", "/director", "/chancellor", "/provost",
                          "office of the"),
            text_mentions("from the dean", "from the director", "office of the dean"),
        ),
        because="Dean or Director communications. Named first among material always "
                "kept from university offices.",
        source="Answer 3.2",
    ),
    Rule(
        name="admin.retain.annual_reports",
        disposition="selected",
        match=any_of(
            folder_named("annual reports", "reports"),
            filename_matches(r"\bannual\s*report\b"),
            text_mentions("annual report"),
        ),
        because="Annual reports from the office. Named as always kept.",
        source="Answer 3.2",
    ),
    Rule(
        name="admin.retain.task_force_reports",
        disposition="selected",
        match=any_of(
            folder_named("task force", "taskforce", "working group", "committees"),
            path_contains("task force", "working group"),
            text_mentions("task force", "working group report"),
        ),
        because="Task force reports. Named as always kept.",
        source="Answer 3.2",
    ),
    Rule(
        name="admin.retain.minutes_and_agendas",
        disposition="selected",
        match=any_of(
            folder_named("minutes", "agendas", "meetings", "faculty meetings"),
            filename_matches(r"\b(minutes|agenda)\b"),
            text_mentions("meeting minutes", "agenda item", "motion carried",
                          "call to order"),
        ),
        because="Meeting minutes and agendas for college or school faculty meetings. "
                "Named as always kept.",
        source="Answer 3.2",
    ),
    Rule(
        name="admin.retain.annual_budgets",
        disposition="selected",
        match=all_of(
            any_of(
                folder_named("budget", "budgets"),
                filename_matches(r"\b(annual\s*budget|budget\s*(fy|20)\d+)\b"),
                text_mentions("annual budget", "budget request", "budget allocation"),
            ),
            # The distinction that matters — see admin.discard.accounting_detail
            not_(any_of(
                folder_named("invoices", "purchasing", "payroll", "timesheets",
                             "expenses", "receipts"),
                path_contains("purchase order", "invoice", "expense report"),
            )),
        ),
        because="Annual budgets. Named as always kept — as distinct from the "
                "transaction-level accounting detail listed as disposable.",
        source="Answer 3.2 (keep) read against 3.3 (discard)",
        notes="The line here is between a budget as a planning document and the "
              "accounting exhaust of executing it. Joanne keeps the first and "
              "discards the second. This rule tries to encode that and is the one "
              "most likely to need correcting.",
    ),
    Rule(
        name="admin.retain.enrollment_statistics",
        disposition="selected",
        match=any_of(
            folder_named("enrollment", "enrolment", "statistics", "institutional research"),
            filename_matches(r"\benroll?ment\b"),
            text_mentions("enrollment statistics", "headcount", "matriculation"),
        ),
        because="Statistics on enrollment. Named as always kept.",
        source="Answer 3.2",
        notes="Aggregate statistics only. Individual student records route to "
              "restricted review via admin.sensitive.student_records, which runs first.",
    ),
    Rule(
        name="admin.retain.curriculum_changes",
        disposition="selected",
        match=any_of(
            folder_named("curriculum", "curricula", "courses", "programs",
                         "program review"),
            path_contains("curriculum change", "course proposal", "new program",
                          "program review"),
            text_mentions("curriculum committee", "course proposal",
                          "program modification"),
        ),
        because="Proposed changes to curricula, courses and goals — drafts as well as "
                "final versions. Named as always kept, explicitly including drafts.",
        source="Answer 3.2 — 'drafts and final versions of proposed changes to "
               "curricula, to courses, to goals, etc.'",
        notes="Note the contrast with personal papers, where drafts are kept only for "
              "humanities scholars. Here they are kept unconditionally, because a "
              "rejected proposal is evidence of what the college considered.",
    ),
]

# ═════════════════════════════════════════════════════════════════ discard ══

DISCARD = [
    Rule(
        name="admin.discard.accounting_detail",
        disposition="discard_candidate",
        match=any_of(
            folder_named("invoices", "purchasing", "purchase orders", "receipts",
                         "expenses", "reimbursements", "p-card", "pcard"),
            path_contains("purchase order", "invoice", "expense report",
                          "reimbursement", "requisition"),
            filename_matches(r"\b(invoice|receipt|po[-_ ]?\d+|req[-_ ]?\d+)\b"),
        ),
        because="Transaction-level accounting detail — purchases and expenditures. "
                "Named as safe to set aside.",
        source="Answer 3.3 — 'accounting details related to general oversight of "
               "budget expenditures such as purchases'",
        notes="Deliberately narrower than 'anything financial'. Annual budgets are "
              "kept; the purchase orders that execute them are not.",
    ),
    Rule(
        name="admin.discard.payroll_and_timesheets",
        disposition="discard_candidate",
        match=any_of(
            folder_named("payroll", "timesheets", "timecards", "time reporting"),
            path_contains("payroll", "timesheet", "timecard", "time report"),
            filename_matches(r"\b(payroll|timesheet|timecard)\b"),
        ),
        because="Payroll records and timesheets. Named as safe to set aside.",
        source="Answer 3.3",
        notes="Sensitivity rules run first, so anything that also reads as a "
              "personnel matter routes to review instead. Salary data on named "
              "individuals is the case to watch — worth asking Joanne whether this "
              "rule should be narrower.",
    ),
    Rule(
        name="admin.discard.system_files",
        disposition="discard_candidate",
        match=any_of(
            folder_named("windows", "system32", "appdata", "programdata", "temp",
                         "tmp", "cache"),
            path_contains("/windows/", "/appdata/", "/program files"),
            ext("dll", "sys", "exe", "msi", "ini", "lnk", "tmp", "bak", "log"),
        ),
        because="Operating system or application file, not an office record.",
        source="Answer 3.3, read across from the personal papers guidance",
        confidence="tentative",
        notes="Joanne listed system files under personal papers rather than "
              "administrative records. Applied here too because office drives carry "
              "the same junk, but it is an extension of what she said rather than "
              "what she said.",
    ),
]

RULESET = Ruleset(
    name="administrative",
    description=(
        "Administrative records from university offices — Chancellor's Files, "
        "President's Office, deans and directors. Drafted from the University "
        "Archives' answers to questions 3.2 and 3.3, August 2026. Turnaround target "
        "is no more than 3 months (answer 8.2), tighter than personal papers."
    ),
    retain=RETAIN,
    discard=DISCARD,
    sensitive=SENSITIVE,
)
