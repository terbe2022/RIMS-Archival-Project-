"""Relevance labels for the SAME corpus under the alternate intake form ACC-SYN-2026-001-B
(teaching, mentoring, service and public-engagement history).

Only relevance changes between forms. Sensitivity, lane, expected action and the reference
descriptions are properties of the file and stay identical, which is exactly what the
two-form test checks.
"""
from __future__ import annotations

import collections
import csv
import json
import re

# Ordered: first match wins. Matched against "<path> || <gt_title>".
RULES = [
    # ---- personal, system, junk stay none (checked first so 'bee' words in them can't promote)
    (r"Documents/Personal/|Pictures/Family/|/Music/|Bee_Movie|beekeeping_supplies|funny_cat|garden_plan|wifi_password|W-4_2020",
     "none", "Personal records and personal media are excluded"),
    (r"Spouse message|Family message|school newsletter|fantasy football|Phishing|vendor sale|Marketing feedback|Parking lot|IT two-factor|Email maintenance|Ethics training",
     "none", "Personal, spam, phishing or routine notices she did not write"),

    # ---- teaching (high)
    (r"Teaching/ENTM210/(ENTM210_Syllabus|old/|lectures/)", "high", "Syllabi and lecture materials from every year she taught"),
    (r"Teaching/ENTM210/(grades|roster)", "none", "Individual student grades and class rosters are excluded (FERPA)"),

    # ---- mentoring (high / moderate)
    (r"Comments on Natarajan dissertation|Natarajan_thesis_backup|thesis_backup/ch3/ch3_draft|thesis_backup/figs\.zip",
     "high", "Records of mentoring graduate students (her chapter comments, theses they produced)"),
    (r"Conference poster acceptance|Preliminary exam scheduling|Student request for recommendation letter",
     "high", "Mentoring records: posters, exam records, recommendation correspondence (FERPA-restricted)"),
    (r"Pan trap protocol version 3", "moderate", "Shows training students in field methods (mentoring), though primarily a research protocol"),
    (r"Student absence notice|bowls for Thursday|Student question about supply", "low", "Routine student logistics; slight evidence of lab life"),
    (r"notes: todo\?|thesis_backup/ch3/latest", "low", "Fragments of a student's working files"),

    # ---- lab life and culture
    (r"lab_meeting_2021-02-18|lab meetings/bombus pilot 2007|Lab_Admin/|lab_logo|Lab member roster",
     "high", "Records of lab life and culture: lab meetings, rosters, safety practices, logo"),
    (r"Penner_PIP|performance concerns", "moderate", "Lab staff personnel matter: documents running the lab, but confidential personnel record"),
    (r"Phone/IMG_20200410|whiteboard", "moderate", "Lab working life (whiteboard session), though research content"),

    # ---- service
    (r"Documents/Service/|Prairie society board|Peer review invitation|FW: Prairie Bee Survey - statewide|Forwarded thread on statewide",
     "high", "Service to department and profession: committees, society board, working group, reviews"),
    (r"support_letter_county_prairie", "moderate", "Early advocacy/service letter for a land acquisition"),

    # ---- public engagement & outreach
    (r"garden_club|Garden club outreach|Interview request|interview request|voicemail_courier|Voicemail from newspaper|Monarch_citizen_science|Newsletter: Pollinator Partners|newsletter issue profiling",
     "high", "Public engagement and outreach: community talks, media, citizen science"),
    (r"oral_history/Ritter_interview|landowner Harold Ritter|history of the remnant prairie|the old prairie on our place",
     "high", "Relationships with landowners (public engagement), including an oral-history interview"),
    (r"bee_approach_animation|Dept_Seminar|Seminar confirmation|seminar\.ics", "moderate", "Talks presenting her work to academic audiences; secondary to outreach"),
    (r"Conference_Program_ESA_2019", "low", "Conference program listing her talk"),

    # ---- career
    (r"Achterberg_CV_2024|README_for_archives|retirement congratulations|Retirement to-do|TODO\.txt", "high",
     "Her curriculum vitae, retirement records, and records summarising her career"),
    (r"Annual_Report_Y|NSF annual project report|notes\.txt$", "moderate", "Grant reports' training and broader-impacts sections document mentoring and outreach"),
    (r"Collaborations/Bonn_2009|Besuch im Juli", "moderate", "International professional engagement"),
    (r"field_contacts\.vcf|lab_roster_and_keys", "moderate", "Contacts and rosters documenting the lab community and outreach network"),
    (r"Travel confirmation", "low", "Travel booking confirmations (routine), shows conference participation"),
    (r"Faculty meeting agenda", "low", "Routine departmental announcement, minimal service evidence"),
    (r"Seminar announcement for another speaker", "none", "Routine announcements she did not write"),
]


def _b_for(lab, cache, labels):
    if lab.path in cache:
        return cache[lab.path]
    if lab.duplicate_of and lab.duplicate_of in labels:
        rel, why = _b_for(labels[lab.duplicate_of], cache, labels)
        res = (rel, why + " (exact duplicate; exclude_duplicate still applies)")
    else:
        hay = f"{lab.path} || {lab.gt_title}"
        res = None
        for pat, rel, why in RULES:
            if re.search(pat, hay):
                res = (rel, why)
                break
        if res is None:
            if lab.relevance == "none":
                res = ("none", "Excluded under either form (system, duplicate, personal or junk)")
            elif lab.lane == "system":
                res = ("none", "Operating-system files and caches")
            else:
                res = ("low", "Research material is appraised under the research accession (ACC-SYN-2026-001)")
    cache[lab.path] = res
    return res


def write(reg, outdir):
    labels = reg.labels
    cache: dict = {}
    rows = []
    for path in sorted(labels):
        lab = labels[path]
        rel_b, why_b = _b_for(lab, cache, labels)
        rows.append({"path": path, "relevance_A": lab.relevance, "relevance_B": rel_b, "relevance_rationale_B": why_b,
                     "changed": "yes" if rel_b != lab.relevance else "no", "gt_title": lab.gt_title,
                     "container": lab.container})
    with open(outdir / "ground_truth_formB.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
    top = [r for r in rows if not r["container"]]
    trans = collections.Counter(f"{r['relevance_A']}->{r['relevance_B']}" for r in top)
    stats = {"form": "ACC-SYN-2026-001-B", "files": len(top), "changed": sum(r["changed"] == "yes" for r in top),
             "by_relevance_B": collections.Counter(r["relevance_B"] for r in top), "transitions_A_to_B": dict(sorted(trans.items()))}
    (outdir / "summary_stats_formB.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=1))
