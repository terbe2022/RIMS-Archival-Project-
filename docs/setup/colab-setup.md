# Shared Colab smoke workflow

Open `notebooks/shared-pipeline-colab.ipynb` from a reviewed GitHub commit.
The notebook resolves its Code ref once to an exact SHA and records it in the report.
For repeat comparisons use that SHA in the Colab Code ref form field. Server
source remains at its deliberately deployed commit; this PR does not deploy it.

## Required clicks

1. Sign in to Google if Colab requests it.
2. For GPU inference, choose Runtime > Change runtime type > GPU. CPU mode
   remains useful: it runs the offline contract check without package installs.
3. Choose Runtime > Run all and accept Colab's notebook execution prompt if shown.
4. Allow the report ZIP download if the browser blocks it. The Files sidebar
   also contains the report at the path printed by the notebook.

No cell editing is needed. Vision is off by default; its optional form checkbox
runs two generated drawings. Each run creates a fresh checkout and report directory.
Use only synthetic inputs; never mount private accession datasets or upload originals.

## Dependency behavior and evidence

The runtime/CUDA check precedes installation. The text stub reads canonical
pipeline prompt literals without importing extraction or model packages and
requires only the Python standard library. GPU runs install a bounded stack
from `validation/colab-requirements.txt` into a separate virtual environment.
This avoids the Transformers 4 / preinstalled Gradio and Diffusers Hub conflict
without upgrading, uninstalling or downgrading Colab kernel packages. The isolated
PyTorch/CUDA download can be large. The environment's pip check must pass before
inference. GPU availability is checked again by the inference harness.

The automatically generated ZIP contains diagnostics, a summary, and only the
synthetic result files produced in that session. Setup failures and skipped
models remain visible; schema failures do not count as success. Versions,
model revisions, prompt hashes and code SHA support reproducibility. Contract
success establishes harness behavior, not description quality, appraisal,
sensitivity recall or operational throughput. Use Tayler's case study methodology
for controlled comparisons and substantive grading; do not transfer its scores.

## Codex CLI with a ChatGPT account: investigation status

Official authentication documentation supports subscription sign-in and
`codex login --device-auth` for headless machines:
https://learn.chatgpt.com/docs/auth

This offers a potential route without usage-based API calls, subject to the
existing account's Codex access, workspace permissions and usage limits.
It is not a verified Colab integration. The available browser was signed out
of Google when inspected; no runtime or CLI execution could be verified there.

Verification must be performed in a private Colab terminal, if available:
install the official `@openai/codex` CLI package from npm; set a temporary
CODEX_HOME outside the checkout/reports; remove API-key variables from that
process; use device authentication; have the user complete sign-in; then run
one bounded synthetic coding/test task and inspect its diff and test evidence.
Do not put login commands, device codes, tokens, authentication output or caches
in notebook cells, GitHub, or downloadable reports. Do not copy local credentials.
If a private terminal is unavailable, this route is blocked rather than verified.
Log out and remove the temporary credential cache after the test. Any source
repair must be returned as a reviewed GitHub PR before a pinned execution run.

No paid API calls were made. Server regression/inference and Colab GPU execution
remain unverified; the recorded server deployment is bed430ee68aa16fffa87ba87f46f2e12d20de3d6.

Local verification: 25 regression tests passed in the existing isolated project test
environment; the pinned model stack installed in a separate Windows environment,
passed pip check and imported torch, torchvision, Transformers pipeline and
Accelerate. This does not verify Linux/Colab CUDA compatibility or GPU inference.
