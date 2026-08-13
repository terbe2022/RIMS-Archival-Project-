"""
rules/personal_papers.py

Drafted from the University Archives' answers of 12 Aug 2026, questions 3.2 and
3.3. **Not confirmed.** This is our reading of what they told us, and the point
of writing it down is so they can correct it.

Their words, 3.2 — always keep:

    For "personal papers" of most faculty: Correspondence with peers,
    collaborators, family, friends – particularly if it references their
    research, participation on committees or boards, courses they taught,
    articles they wrote, grant applications they received, grant reports, books
    they wrote. For some faculty – humanities scholars, English professors for
    example – the drafts of their final published works would be valuable to
    keep.

Their words, 3.3 — nearly always set aside:

    For "personal papers": Everything related to the system operations including
    MOST software applications that the person may have loaded onto their
    computer. Any personal finance info, personally loaded up commercial
    entertainment.

Note "MOST software applications" and "most faculty" — the guidance is
deliberately hedged, which is why nothing here discards without sampling.
"""
from .base import (Rule, Ruleset, ext, path_contains, folder_named,
                   filename_matches, text_mentions, any_of, all_of, not_,
                   profile_field_in)

# ═══════════════════════════════════════════════════════════════ sensitive ══
# Evaluated first, and a match here beats every retain and discard rule.
# Answer 3.3 lists personal finance as disposable; it is also the strongest
# PII signal on a personal drive. Treated as sensitive, not as discard.

SENSITIVE = [
    Rule(
        name="pp.sensitive.personal_finance",
        disposition="restricted_review",
        match=any_of(
            folder_named("finance", "financial", "banking", "taxes", "tax"),
            path_contains("/tax", "bank statement", "brokerage", "mortgage",
                          "credit card", "1040", "w-2", "w2 form"),
            filename_matches(r"\b(tax|taxes|1099|1040|w-?2)\b"),
        ),
        because="Personal financial material. The Archives lists this as normally "
                "disposable, but it carries personal information, so a person "
                "decides rather than a rule.",
        source="Answer 3.3, plus PII precedence",
        notes="Joanne listed personal finance under 'set aside'. We route it to "
              "review rather than disposal because discarding unread financial "
              "records is not recoverable. Worth confirming she is happy with that.",
    ),
    Rule(
        name="pp.sensitive.medical",
        disposition="restricted_review",
        match=any_of(
            folder_named("medical", "health"),
            path_contains("fmla", "medical leave", "health record", "diagnosis"),
        ),
        because="Medical or health-related material. Always reviewed by a person.",
        source="Standing sensitivity policy, not from 3.3",
    ),
    Rule(
        name="pp.sensitive.student_records",
        disposition="restricted_review",
        match=any_of(
            folder_named("grades", "students", "transcripts"),
            path_contains("grade book", "gradebook", "transcript", "letter of rec"),
            text_mentions("FERPA"),
        ),
        because="Possible student records, which are FERPA-covered. Reviewed by a "
                "supervising archivist before any disposition.",
        source="FERPA obligation; not raised in 3.3 but unavoidable in faculty material",
        notes="A faculty drive will contain grading material. This rule is broad "
              "on purpose — over-routing to review is recoverable.",
    ),
]

# ══════════════════════════════════════════════════════════════════ retain ══
# Order matters. Correspondence first because answer 3.2 names it before
# anything else and it is the highest-value category on a personal drive.

RETAIN = [
    Rule(
        name="pp.retain.correspondence",
        disposition="selected",
        match=any_of(
            ext("eml", "msg", "pst", "ost", "mbox"),
            folder_named("correspondence", "letters", "email", "emails", "mail"),
            path_contains("/correspondence", "/letters"),
        ),
        because="Correspondence. The Archives names this first among material always "
                "worth keeping, particularly where it touches research, committees, "
                "teaching or publications.",
        source="Answer 3.2",
        notes="Deliberately broad. Answer 1.7 confirms .eml and .pst arrive inside "
              "personal papers accessions, so this rule is also what routes email "
              "into the main line rather than a separate phase.",
    ),
    Rule(
        name="pp.retain.grants",
        disposition="selected",
        match=any_of(
            folder_named("grants", "grant", "funding", "proposals", "nsf", "nih"),
            path_contains("/grant", "grant report", "grant application"),
            text_mentions("grant application", "grant report", "award notice",
                          "principal investigator", "NSF", "NIH"),
        ),
        because="Grant applications and grant reports. Named explicitly as always kept.",
        source="Answer 3.2",
    ),
    Rule(
        name="pp.retain.publications",
        disposition="selected",
        match=any_of(
            folder_named("publications", "papers", "articles", "books", "manuscripts"),
            path_contains("/publication", "/manuscript", "/book"),
            text_mentions("manuscript", "peer review", "accepted for publication"),
        ),
        because="Articles and books the person wrote. Named as always kept.",
        source="Answer 3.2",
    ),
    Rule(
        name="pp.retain.committees_and_service",
        disposition="selected",
        match=any_of(
            folder_named("committee", "committees", "board", "boards", "service"),
            path_contains("/committee", "task force", "advisory board"),
            text_mentions("minutes", "agenda", "task force", "advisory committee"),
        ),
        because="Participation on committees and boards. Named as always kept.",
        source="Answer 3.2",
    ),
    Rule(
        name="pp.retain.teaching",
        disposition="selected",
        match=any_of(
            folder_named("teaching", "courses", "syllabi", "lectures"),
            path_contains("/course", "/teaching", "syllabus"),
            text_mentions("syllabus", "course description", "lecture notes"),
        ),
        because="Material about courses taught. Named as always kept.",
        source="Answer 3.2",
        notes="Distinct from grading material, which is sensitive — the sensitivity "
              "rules run first, so a gradebook inside a teaching folder still routes "
              "to review.",
    ),
    Rule(
        name="pp.retain.research",
        disposition="selected",
        match=any_of(
            folder_named("research", "data", "fieldwork", "lab", "notebooks"),
            path_contains("/research", "/fieldwork", "lab notebook"),
        ),
        because="Research material. Answer 3.2 treats research as the thing that "
                "makes other categories valuable, so it is retained in its own right.",
        source="Answer 3.2, inferred",
        confidence="tentative",
        notes="Inferred rather than stated. Joanne named correspondence *referencing* "
              "research; she did not explicitly say research files themselves. "
              "Please confirm.",
    ),
    # ── the discipline-conditional rule ──────────────────────────────────────
    Rule(
        name="pp.retain.drafts_humanities",
        disposition="selected",
        match=all_of(
            profile_field_in("humanities", "english", "history", "literature",
                             "philosophy", "classics", "arts"),
            any_of(
                folder_named("drafts", "draft", "versions", "revisions"),
                filename_matches(r"\b(draft|rev\d*|v\d+|version\s*\d+)\b"),
            ),
        ),
        because="Drafts of published work, for a humanities scholar. The Archives "
                "singles these out as valuable for this group specifically.",
        source="Answer 3.2 — 'for some faculty, humanities scholars, English "
               "professors for example, the drafts of their final published works "
               "would be valuable to keep'",
        notes="This is why the accession profile matters. The same file is kept for "
              "an English professor and set aside for a chemist. `profile_field` on "
              "the accession record selects which applies. If it is missing, this "
              "rule cannot fire and the file falls through to review.",
    ),
]

# ═════════════════════════════════════════════════════════════════ discard ══
# Only reached if nothing above matched. Everything here is path-and-format
# detectable with no inference, which is the cheap end of the pipeline.

DISCARD = [
    Rule(
        name="pp.discard.system_files",
        disposition="discard_candidate",
        match=any_of(
            folder_named("windows", "system32", "syswow64", "appdata", "programdata",
                         "$recycle.bin", "system volume information", "library",
                         "temp", "tmp", "cache", "caches"),
            path_contains("/windows/", "/appdata/", "/program files", "/system32/",
                          "/.cache/", "/recycle"),
            ext("dll", "sys", "exe", "msi", "cab", "ini", "lnk", "dat", "log",
                "tmp", "bak"),
        ),
        because="Operating system or application file, not a record the person created.",
        source="Answer 3.3 — 'everything related to the system operations'",
    ),
    Rule(
        name="pp.discard.installed_software",
        disposition="discard_candidate",
        match=any_of(
            folder_named("program files", "program files (x86)", "applications",
                         "installers", "downloads"),
            ext("dmg", "pkg", "deb", "rpm", "iso", "msi"),
            filename_matches(r"\b(setup|installer|install)\b"),
        ),
        because="Software the person installed on their own machine.",
        source="Answer 3.3 — 'MOST software applications that the person may have "
               "loaded onto their computer'",
        confidence="tentative",
        notes="Joanne said MOST, not all. If a researcher wrote or heavily customised "
              "software, that is scholarly output and this rule would be wrong. "
              "Sampled harder because of the hedge.",
    ),
    Rule(
        name="pp.discard.commercial_entertainment",
        disposition="discard_candidate",
        match=any_of(
            folder_named("music", "itunes", "movies", "videos", "games", "steam",
                         "spotify", "podcasts"),
            ext("mp3", "m4a", "aac", "flac", "wma", "mkv", "avi", "torrent"),
        ),
        because="Commercial entertainment the person loaded themselves.",
        source="Answer 3.3 — 'personally loaded up commercial entertainment'",
        notes="Deliberately does not include .mp4 or .mov. Both are in the Archives' "
              "confirmed format list (answer 1.7) and are as likely to be recorded "
              "lectures or fieldwork as entertainment. Folder context decides those.",
    ),
    Rule(
        name="pp.discard.browser_artifacts",
        disposition="discard_candidate",
        match=any_of(
            folder_named("cookies", "history", "bookmarks", "browser"),
            path_contains("/chrome/", "/firefox/", "/safari/", "webcache"),
        ),
        because="Browser artefacts. System operations material rather than a record.",
        source="Answer 3.3, inferred from 'system operations'",
    ),
]

RULESET = Ruleset(
    name="personal_papers",
    description=(
        "Personal papers of faculty and alumni. Drafted from the University "
        "Archives' answers to questions 3.2 and 3.3, August 2026. Correspondence "
        "is the highest-value category. Turnaround target is 3–6 months from "
        "receipt (answer 8.2), so there is no reason to prefer speed over care."
    ),
    retain=RETAIN,
    discard=DISCARD,
    sensitive=SENSITIVE,
)
