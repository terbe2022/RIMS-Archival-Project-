# Teams program-manager workflow

The shared agent coordinates RIMS from the designated Tayler-Gauri project chat and GitHub evidence. Tayler demonstrated opening the published agent, GitHub issue retrieval and selected-chat retrieval in supplied October 6 results. Gauri is listed as an authorized user. She reports granting GitHub and Teams connection permissions, but the supplied launch link fails for her. Joint use remains unresolved; permission consent is not a successful launch test.

## Current interaction

Post project updates in the designated chat. Ask the agent to retrieve a bounded period from that selected chat, classify reported progress, decisions, suggestions, blockers and questions, and match relevant existing issues. Preserve message IDs and timestamps. Owners, dates and approvals absent from evidence remain unknown. A reported completion needs acceptance evidence before changing issue state.

Example update:

> Validation update: I ran the first synthetic Qwen experiment on commit <commit>. Results are in <review link>. Two outputs failed schema checks. I have not tested real records. Next I propose investigating those failures; no deadline is agreed.

Example request:

> Read only our designated RIMS chat since <timestamp>. Summarize project updates with message IDs, match existing issues, and draft exact GitHub changes for review. Do not submit changes yet.

After review, approve a specific proposal rather than an unspecified update. Submission requires an available authorized executor and independent validation under the update contract. GitHub search does not establish write capability. The agent must return actual tool receipts before claiming a change succeeded.

## Requested automation versus demonstrated behavior

Publishing the agent does not automatically add it to an existing one-to-one chat or make it continuously listen. Reading updates as they arrive requires a configured trigger or polling workflow scoped to the selected chat, durable restricted checkpoints, pagination handling, edits and duplicate handling, and reviewed execution controls. These capabilities have not been verified. Instructions alone cannot establish persistence or background monitoring.

Use each user's own authorized connections and confirm Gauri can launch and read permitted sources. Do not share credentials or place private chat IDs, setup tokens or transcripts in public documentation. Keep unrelated conversation out of proposals; restricted records require an approved handling route.

See [repository role controls](PROGRAM-MANAGER.md) and [validation program-manager guidance](../validation/PROGRAM-MANAGER.md).
