#!/usr/bin/env bash
# Creates the label set. Run once. Safe to re-run - existing labels are skipped.
set -u
REPO="terbe2022/RIMS-Archival-Project-"
mk(){ gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force; }

# Pipeline stage - which part of the system
mk "stage:00-source"      "5B4A8C" "Source & access - getting the bytes reachable"
mk "stage:01-inventory"   "2C6A5C" "Inventory & identify - walk, hash, format ID"
mk "stage:02-triage"      "8E6410" "Triage & appraisal - what is worth keeping"
mk "stage:03-extraction"  "25445F" "Extraction & routing - format lanes"
mk "stage:04-enrichment"  "25445F" "Enrichment - PII, summary, description"
mk "stage:05-metadata"    "8E6410" "Metadata - Dublin Core, IPTC, provenance"
mk "stage:06-index"       "4C544E" "Index, search & delivery"
mk "stage:07-scale"       "4C544E" "Scale & scheduling"

# Type - what kind of work
mk "type:build"     "0E8A16" "Write code"
mk "type:research"  "1D76DB" "Investigate, evaluate, measure"
mk "type:decision"  "5319E7" "A choice that needs making and recording"
mk "type:question"  "D4C5F9" "Needs an answer from someone"
mk "type:bug"       "D73A4A" "Something is broken"
mk "type:docs"      "C5DEF5" "Documentation"
mk "type:setup"     "BFD4F2" "Environment and tooling"

# Waiting on - filter by these before a meeting to get your agenda
mk "needs:joanne"     "A8321F" "Blocked on Joanne Kaczmarek"
mk "needs:brent"      "A8321F" "Blocked on Brent West"
mk "needs:bethany"    "A8321F" "Blocked on Bethany Anderson"
mk "needs:privacy"    "A8321F" "Blocked on Data Privacy & Governance"
mk "needs:infra"      "A8321F" "Blocked on Infrastructure / sysadmins"
mk "needs:supervisor" "A8321F" "Blocked on supervisor approval"

# Priority
mk "blocker"   "B60205" "Blocks other work - fix first"
mk "good-first-issue" "7057FF" "Good entry point"
echo "Labels done."
