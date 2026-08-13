"""
Quick behavioural checks on the rulesets. Run: python -m schema.rules.test_rules
Not a full test suite — these assert the properties that would be dangerous to
get wrong, and the ones an archivist would notice.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from schema.rules import ruleset_for, evaluate


def row(path, atype="personal_papers", profile=None, **kw):
    d = {"path_norm": path, "path_norm_ci": path.lower(),
         "filename": path.split("/")[-1],
         "extension": path.rsplit(".", 1)[-1].lower() if "." in path.split("/")[-1] else "",
         "profile_field": profile, "s02_keywords": [], "s02_peek_text": ""}
    d.update(kw)
    return d, ruleset_for(atype)


def decide(*a, **k):
    r, rs = row(*a, **k)
    return evaluate(r, rs)


FAILS = []
def check(desc, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'}  {desc}\n      got {got!r}, want {want!r}" if not ok
          else f"PASS  {desc}")
    if not ok:
        FAILS.append(desc)


# The property that matters most: sensitivity beats discard.
check("HR discipline file is not discarded",
      decide("hr/discipline/grievance.docx", "administrative")["s02_decision"],
      "restricted_review")
check("payroll under personnel is not discarded",
      decide("personnel/payroll/salaries.xlsx", "administrative")["s02_decision"],
      "restricted_review")
check("plain payroll folder IS discardable",
      decide("finance/payroll/timesheet_week12.xlsx", "administrative")["s02_decision"],
      "discard_candidate")

# The discipline gate.
check("drafts kept for a humanities scholar",
      decide("drafts/chapter3_v2.docx", profile="humanities")["s02_decision"],
      "selected")
check("same drafts not kept for a chemist",
      decide("drafts/chapter3_v2.docx", profile="chemistry")["s02_decision"],
      "not_selected")
check("missing profile_field falls through, does not discard",
      decide("drafts/chapter3_v2.docx", profile=None)["s02_decision"],
      "not_selected")

# Budget vs accounting detail — the line we are least sure of.
check("annual budget is kept",
      decide("budget/annual_budget_FY19.xlsx", "administrative")["s02_decision"],
      "selected")
check("purchase order is set aside",
      decide("budget/invoices/PO-1234.pdf", "administrative")["s02_decision"],
      "discard_candidate")

# Curriculum drafts are unconditional in administrative.
check("curriculum draft kept without a profile",
      decide("curriculum/new_program_draft.docx", "administrative")["s02_decision"],
      "selected")

# Email routing.
check(".pst routes to correspondence",
      decide("archive/outlook_backup.pst")["s02_rule_matched"],
      "pp.retain.correspondence")

# The default must never be discard.
check("unmatched file is not_selected, not discarded",
      decide("stuff/thing.qqq")["s02_decision"],
      "not_selected")

# mp4 is not entertainment by extension alone — answer 1.7 has it in the
# confirmed format list and it is as likely to be a recorded lecture.
check("mp4 outside a media folder is not auto-discarded",
      decide("fieldwork/interview_recording.mp4")["s02_decision"] != "discard_candidate",
      True)

print()
print(f"{len(FAILS)} failure(s)" if FAILS else "all checks passed")
sys.exit(1 if FAILS else 0)
