# Experiment: <name>

Status: design draft — not run
Owner: Gauri
Issue: <GitHub issue URL>
Design frozen: <date/commit, after review>

## Question and scope

<Model comparison or context ablation; distinguish description from appraisal.>

Data: synthetic only for cloud runs. Fixture revision/hash: <value>.
Cases: <number and selection/strata>; exclusions: <predefined reasons>.

## Conditions held constant

- Repository commit and fixture seed/hash: <values>
- Prompt text/hash and output contract: <values>
- Model identifiers/revisions/licences: <values>
- Serving stack, dependency versions, hardware: <values>
- Decoding, quantization, output limit, repeats: <values>
- Scheduling, warm-up and timing convention: <values>
- For context ablation: paired case IDs and permitted context fields; never valuable/exclude.

## Metrics and acceptance criteria

Report tolerant JSON parseability separately from schema validity. Define explicit
abstention and its labelled cases; exact-response consistency; timing and failure
counts. Define treatment of timeouts, parse errors and missing measurements.
Agree rejection criteria before running; historical rubric thresholds conflict.
Do not average the four quality dimensions into a single score.

## Independent model judging

<Sample selection, judge model IDs/revisions, blinded keys, full-source access, adjudication,
agreement measure, and key custodian. Do not include the key in the grader sheet.>

## Artifact handling and limits

<Synthetic artifact location, privacy review, notebook-output clearing, report
path. Real University follow-up is a separately approved experiment.>

## Deviations

<Record changes after design freeze; distinguish exploratory reruns from baseline.>
