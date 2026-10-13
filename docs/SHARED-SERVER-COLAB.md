# One codebase for the server and Colab

October 13 execution update: investigate the reported University Nemotron NIM API
as the initial shared compute route. Gauri access is unverified. Colab is optional
synthetic fallback, not a required setup. See [current access plan](../validation/API-ACCESS.md).
Existing server/Colab procedures below apply only to their named environments;
the NIM host is a separate service. No service change or access grant is implied.

GitHub main is the reviewed source of pipeline code. The server deploys a recorded commit using scripts/deploy_code.py. Colab clones GitHub and checks out a commit before importing the same text and vision prompts. Data and model-serving environments remain separate.

## Current repair

The October 13 server audit found a malformed vision prompt in both the live code and old server clone. This integration fixes it, adds the missing workbench.schema compatibility path, and brings reviewed pipeline safety repairs into the current source without reverting the protected website. Public payload synchronization remains disabled. The old server clone predates the repository history rewrite and must not be pulled or pushed.

## Server deployment

Clone into a new directory, never on top of the old clone or live pipeline. From the fresh clone, run `python3 scripts/deploy_code.py --live /var/advanalytics/datashare/Admin-pipeline/pipelines/archivist_triage_tool` first. Review its dry run, then repeat with `--apply`. The command requires clean tracked code, parses Python before applying, backs up changed code and verifies hashes afterward. Use `--verify` to check parity. Rollback uses `--rollback /absolute/path/to/the/printed/journal.json`.

The live pipeline gains the canonical src/ layout. Updated entrypoints prioritize that code. Legacy workbench/, web/review.html and web/workbench.html remain preserved; they are not deleted or asserted equivalent to the current accession workbench. Data, intake forms, run artifacts, decisions, state files, models and secrets are not copied into GitHub or overwritten by deployment. Inspect notebooks or external launchers that still import the legacy directory before using them.

Run `python3 -B tests/test_pipeline_repairs.py` and `python3 -B tests/test_shared_runtime.py` in the fresh clone. This is offline regression testing, not a GPU result. Existing dependencies must be installed in the chosen interpreter; do not replace the server environment indiscriminately. The audit reported python-pptx missing, which matters for PPTX extraction. Obtain an approved environment/install path before changing it.

The audit found Ollama responsive on 11434 and vLLM on 8000; it did not establish GPU performance. Port 11435 was unavailable. Do not start/restart services automatically. A short synthetic text smoke comparison can use an explicitly chosen existing endpoint:

```
python3 -B validation/pipeline_model_compare.py --backend ollama --url http://127.0.0.1:11434 --models llama3.1:8b --out local-runs/server-text-smoke.json
```

This command makes three synthetic requests. Review failures and latency before a real workload. It does not test every extraction format, run the full archive, or prove appraisal accuracy.

## Gauri's Colab workflow

Open [the shared notebook](https://colab.research.google.com/github/terbe2022/RIMS-Archival-Project-/blob/main/notebooks/shared-pipeline-colab.ipynb), select a GPU, and run setup. main is resolved once per session; record the resulting commit and use that SHA for repeats. Start with the offline stub check and one small Qwen text model. An optional small vision model uses generated drawings. Change only the model list for an initial comparison. Run candidates sequentially.

Reports include code commit, tracked-code modifications, model revisions (Hugging Face), dependency versions, prompt hashes, timestamps, output/error records and elapsed time. Schema adherence and simple synthetic expected-field checks are separate. Review description quality with the agreed rubric; these few smoke fixtures are not the full model-selection experiment. No model superiority has been measured by creating this notebook.

No paid model API is used. Colab GPU availability is not guaranteed. Actual Colab/GPU model execution remains unverified until Gauri runs it. Original accession material remains prohibited in Colab under validation/AGENTS.md; private GitHub access is not approval to upload it there.

The existing recovery notebook and larger validation harness remain under their open PR. This shared integration notebook does not overwrite Gauri's work. Submit experiment designs and reviewed synthetic results on gauri/* branches through PRs; keep raw run artifacts in ignored local-runs/ and clear notebook outputs.

## Original website descriptions

The audit located demo/aw/prototype-data.json with 2,375 populated descriptions and zero withheld-description placeholders. Transfer that export into the local private staging directory for inspection, not into the public repository. Verify its provenance, fields, count and sensitivity before replacing the authenticated metadata snapshot. This deployment does not change website data or its shared password.
