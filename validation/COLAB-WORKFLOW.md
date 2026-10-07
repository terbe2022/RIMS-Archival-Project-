# Gauri's integrated browser workflow

Gauri writes/runs notebooks in Colab. GitHub stores versioned notebooks, helper
Python code, experiment protocols and reviewed results. The program manager
reads GitHub and proposes document/work updates. Codex Cloud can supply that
tool-enabled role if available in her account; no local Codex installation is
assumed. Runtime execution and project management are separate capabilities.

## One experiment from start to finish

1. After the recovery/workspace branch is published, open GitHub and create a
   gauri/<experiment> branch from the reviewed integration base. Have the manager
   read its issue and draft validation/experiments/<experiment>.md. Gauri approves
   cases, prompt, repeats, metric choices and planned model judging.
2. In Colab: File -> Open notebook -> GitHub; select the repository, exact branch,
   and notebooks/colab-model-evaluation.ipynb. Work in a synthetic-only copy.
   Record that branch and its actual commit. Enable a suitable GPU when available.
3. Set Edit -> Notebook settings -> Omit code cell output when saving this notebook.
   Also clear execution counts before Git publication and verify the saved file.
   Do not mount a Drive containing real accession material for this experiment.
4. Review the dependency/model-download cells. The clone cell must load the same
   published experiment branch, not silently clone old main. The recovered guide
   gives the recovery-branch example; substitute Gauri's exact experiment branch.
   Record the helper-code commit. A Colab notebook copy and its cloned helper code
   are two copies; saving one does not synchronize the other.
5. Run the offline test file in the synthetic clone, then one smoke case, then the
   agreed comparison. Never paste credentials into cells. No paid API runs while
   funding is pending. Save failures and actual settings; do not edit baseline
   prompts mid-run without recording a new condition.
6. Save/download the notebook with outputs/counts removed. If Colab exposes Save
   a copy in GitHub, select Gauri's exact branch and notebook path; personally
   approve OAuth access. Otherwise download .ipynb and use GitHub's upload-files
   UI on that branch. Never upload a raw run folder indiscriminately.
7. Helper .py files edited inside the Colab runtime do not save through the
   notebook menu. Download the explicit changed files, inspect them, and upload
   to the same branch via GitHub UI, or ask the coding agent to prepare their
   reviewed changes separately. Avoid tokens in notebooks for git push.
8. Preserve synthetic run evidence before the temporary runtime expires. Publish
   only reviewed synthetic summaries/examples in validation/results/<experiment>.md.
   Keep the blind sheet/key separate while grading. Use full source for graders.
9. Tell the manager the commit/report paths. It reads the saved branch, checks
   protocol compliance, drafts project-status/issue/board changes and opens a PR
   only after Gauri authorizes publication. Tayler reviews code/integration.
10. On merge, manager records actual evidence and agreed board state; the next
    experiment starts from the new reviewed base. No task automatically becomes
    complete merely because the notebook ran.

## First supervised session acceptance

- Gauri can read the repo and save a harmless notebook/protocol change to her branch.
- Manager can read the saved change and demonstrate a reversible checkout edit.
- GPU/model access and one synthetic smoke output are demonstrated, not assumed.
- Notebook source contains no stored outputs/counts or secrets.
- Report includes model/revision, fixture/hash, commit, sample and failure counts.
- Issue/Project capability and any missing permissions are explicitly recorded.

Colab runtimes are temporary and saving a notebook does not preserve custom
runtime files. Loading/sharing a notebook can include code, comments and outputs;
the output-omission setting is only one check. See [official Colab FAQ](https://research.google.com/colaboratory/faq.html).

Current grading route: [FRONTIER-JUDGING.md](FRONTIER-JUDGING.md). No blind human grading is planned for synthetic model comparison; independent archivist policy/gold-set work remains separate.
