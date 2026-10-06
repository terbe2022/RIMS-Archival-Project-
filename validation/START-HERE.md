# Gauri's model testing workspace

Owner: Gauri. Prepared 2026-10-06. Model results: not yet measured.

Starting runtime approved by Tayler: Colab with synthetic open-weight fixtures.
Paid model APIs are deferred pending funding. Gauri uses a University computer;
local software installations are not assumed or required for this starting route.

This is your lane for model comparison, context experiments and pipeline
validation. Start with synthetic fixtures. The detailed program is in
[PLAN.md](PLAN.md); operating rules are in [AGENTS.md](AGENTS.md).

For account/tool setup read [GAURI-ONBOARDING.md](GAURI-ONBOARDING.md). Role
definitions and the starter prompt are in [AGENT-ROLES.md](AGENT-ROLES.md).
Use [GRADING.md](GRADING.md) for the proposed operational rubric and
[API-ACCESS.md](API-ACCESS.md) for provider access, secrets and run-budget planning.

Daily Colab/GitHub handoffs: [COLAB-WORKFLOW.md](COLAB-WORKFLOW.md).
Repository and Project coordination: [PROGRAM-MANAGER.md](PROGRAM-MANAGER.md).

## First session

1. Your existing collaborator access is confirmed by Tayler. Use the validation
   recovery branch linked in this guide and confirm the expected files are present
   on GitHub before opening Colab. Record the commit you actually use.
2. Work on a gauri/<experiment-name> branch. Read the root AGENTS.md. Real
   accession material, filenames, manifests and mapping vaults never enter Colab.
3. Copy [the experiment template](experiments/TEMPLATE.md) to a named experiment
   document. Agree metrics/rejection thresholds before comparing models. Do not
   guess the conflicting historical rubric thresholds.
4. Run the offline regression checks from the repository root:

   ```text
   python -B validation/test_recovered_harness.py
   ```

   These use synthetic fixtures and a stub. Passing them is not a model result.
5. For synthetic cloud testing, use
   [the Colab notebook](../notebooks/colab-model-evaluation.ipynb). In Colab choose
   File -> Open notebook -> GitHub, select the repository and the published
   validation branch (or main after merging), then that notebook. Confirm a GPU
   runtime and review dependency/model-download cells before running them.
6. The notebook's clone cell currently clones the default branch. If the recovery
   PR is not merged, change that cell to clone the published recovery branch:

   ```text
   !git clone --branch gauri/validation-kit-recovery-2026-10-06 --single-branch https://github.com/terbe2022/RIMS-Archival-Project-.git
   ```

   Record the actual commit used. Do not paste GitHub passwords/tokens into cells.
   For a private repository, use an approved interactive access workflow.
7. Run one candidate at a time on the same 54 fixtures and fixed prompt/settings after a two-case smoke check.
   Record model revision, licence, dependencies, GPU and configuration. Preserve
   failures, not just favorable outputs. Results are preliminary evidence about
   observed failure shapes, not a guarantee for real accessions.
8. Save synthetic run artifacts outside Git under local-runs/. The current
   notebooks write to an evaluation directory; move only verified synthetic
   artifacts into local-runs/ or retain them in the experiment runtime. Review
   before exporting anything. Keep the blind grading key separate from graders.
9. Use the [rubric](../docs/description-grading-rubric.md) for frontier-model grading.
   Graders need the full synthetic source, not only the displayed opening.
   Record accuracy, genre, specificity and restraint separately.
10. Complete a [result report](results/TEMPLATE.md), clear notebook outputs and
    execution counts, review the Git diff, and open a PR. Link the experiment to
    its GitHub issue; task status lives there, not in another Markdown TODO list.

## University-only follow-up

[The server notebook](../notebooks/model-evaluation.ipynb) can read real manifests
and is for approved University execution only. Check actual paths, data access,
service ownership and run authorization first. Its Ollama startup example does
not authorize starting a service. Do not use it in Colab with real inputs.
No server connection or access grant is included in this workspace setup.

After model comparison, pre-register the paired context experiment. The supplied
notebooks do not implement it yet. Gold-set validation follows independently;
model selection does not establish appraisal-policy accuracy.

## What to share

Share reviewed protocols, code, synthetic aggregate results and failure examples
with provenance through PRs. Do not commit local-runs/, model weights, credential
files or real runtime artifacts. No experiment has been run by creating this
workspace. Tayler reviews engineering implications; Gauri owns evaluation.

Current grading route: [FRONTIER-JUDGING.md](FRONTIER-JUDGING.md). No blind human grading is planned for synthetic model comparison; independent archivist policy/gold-set work remains separate.


For the exact first smoke run, use [FIRST-EXPERIMENT.md](FIRST-EXPERIMENT.md). It distinguishes the harness contract from proposed metadata tasks.

