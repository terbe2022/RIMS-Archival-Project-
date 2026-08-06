#!/usr/bin/env bash
set -u
REPO="terbe2022/RIMS-Archival-Project-"
mk(){ gh api "repos/$REPO/milestones" -f title="$1" -f description="$2" --silent 2>/dev/null \
      && echo "created: $1" || echo "exists or failed: $1"; }
mk "M1 - Foundations"        "Manifest schema, environment setup, software evaluation. Nothing else starts until this lands."
mk "M2 - First pass working" "Stages 00-02 running end to end on the pilot corpus, with real reduction numbers."
mk "M3 - Enrichment"         "Stages 03-05. Extraction lanes, PII, summarisation, metadata."
mk "M4 - Delivery"           "Stage 06. Search, browse, review interface."
mk "M5 - Scale"              "Stage 07. Throughput model, sizing calculator, processing schedule."
