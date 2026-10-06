# Validation kit recovery — 2026-10-06

Recovered from the October 6 transfer ZIP; notebook line breaks repaired. The
original notebooks already had zero outputs/counts; those fields remain empty.
The corpus has 54 synthetic cases and 16 explicit abstention labels. The Colab
notebook compares all cases. The server notebook requires approved University
execution if real rows are used. Neither notebook was run for this recovery.

Run the offline regression checks with Python -B validation/test_recovered_harness.py.
All model calls in those tests use a stub. No installation or model download is required.

The harness measures tolerant parseability, title/description field usability,
explicit readable:false refusal, full parsed-response repeat consistency and
timing. It is not a full JSON-schema validator or a production cost benchmark.
The grading function returns an internal _key; remove it before sharing the blind
sheet, as the notebooks do. First recorded repeat is used, never best-of-repeat.
Full source input is available to graders; shorten only for display, not grading.

No dedicated context-ablation runner, completed evaluation, vision-image corpus,
gold set or schema-parquet fixture is supplied. Synthetic fixtures reproduce
observed failure modes and provide useful screening evidence; passing them does
not guarantee real-corpus performance. Original rubric selection thresholds conflict
and need agreement before experiments. stage06.py remains an unintegrated proposal
and is excluded. Notebook sync needs an explicit per-file output-checking change;
no sync script or server deployment is modified here.
