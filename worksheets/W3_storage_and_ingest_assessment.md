# Storage & Ingest — Assessment Worksheet

**Owner:** Tayler Erbe
**Purpose:** Working document for me to fill in before taking this to Data Privacy, Records
Management, and Infrastructure. Everything here needs an answer from someone before we can
design the front of the pipeline.
**Status:** Not started.

---

## The problem I'm solving

A drive arrives. It contains an unknown number of files — could be ten thousand, could be
millions — belonging to a former faculty or staff member. Before anything else can happen, I
need the bytes to be somewhere the pipeline can read them, and I need to be able to do that
without personally driving to a building every time.

Right now everything we've built has run against small samples pulled through Box. That has
hidden every problem that appears at drive scale, and it means our throughput estimates are
guesses.

This is currently the top blocker on the whole project.

---

## Part 1 — Ingest options

For each option: what it would look like, what it costs, what it needs from other people.

### Option A — Direct attach to a networked workstation

Drive plugs into a machine on the university network that I can reach remotely.

> **What it would take:**
>
> **Who owns that machine:**
>
> **Remote access method available (RDP / VPN / SSH):**
>
> **Blockers:**

### Option B — SMB / NFS network share

Drive contents copied once to a share, pipeline reads over the network.

> **Available share options:**
>
> **Capacity and cost:**
>
> **Read throughput over the network — is it fast enough to hash millions of files:**
>
> **Blockers:**

### Option C — Forensic disk image (E01 / AFF)

Image the drive with a write-blocker, then mount the image read-only for processing.

> **Do we have a write-blocker:**
>
> **Does the nature of these accessions warrant forensic imaging, or is a verified copy enough:**
>
> **Who would do the imaging:**
>
> **Storage cost — an image is the full size of the drive:**

### Option D — University research storage

> **What services exist (Illinois research storage, NCSA, Library storage):**
>
> **Cost model:**
>
> **Can the processing host mount it directly:**
>
> **Who to ask:**

### Option E — Box (current approach)

> **What actually breaks at scale (API limits, download time, path reconstruction):**
>
> **Is Box acceptable as a delivery layer even if not as an ingest layer:**
>
> **Storage quota available:**

### Option F — Azure Blob

We have Azure resources. Note this is only about *storage* — see Part 4 on why hosted AI
services are not on the table for this content.

> **Cost at the volumes involved:**
>
> **Does moving this content to cloud storage clear Data Privacy:**
>
> **Egress cost if we process on-prem:**

---

## Part 2 — Questions for Data Privacy & Governance

These drives will contain personal email, medical and tax records, student records covered by
FERPA, and PII that has never been reviewed. I need answers before content moves anywhere.

**Custody and handling**

1. What is the approved chain of custody for media containing unreviewed PII?

> Answer / who said it / date:

2. Does copying a drive to university network storage constitute a disclosure requiring notice or approval?

> Answer:

3. Are there categories of content that must not leave a specific physical or network boundary?

> Answer:

4. What are the requirements for encryption at rest and in transit for this material?

> Answer:

5. Who is the data steward or custodian of record for an accession like this — the Archives, RIMS, or the originating unit?

> Answer:

**Retention and disposal**

6. Does our "quarantine, never delete" approach satisfy retention obligations, or is there a schedule that requires actual disposal?

> Answer:

7. Who has authority to approve deletion, and at what granularity?

> Answer:

8. Are any of these accessions subject to litigation hold or open FOIA request?

> Answer:

**Access**

9. Who may see unreviewed content during processing? Does Gauri's role permit it? Does mine?

> Answer:

10. Is there a training or agreement requirement before handling this material?

> Answer:

11. What are the rules for deceased individuals' material — do donor agreements or estate restrictions apply?

> Answer:

**AI processing**

12. Is processing this content with locally-hosted open-weight models on university hardware acceptable, given nothing leaves our infrastructure?

> Answer:

13. Is there any circumstance under which content could be sent to a hosted AI service, or is that categorically excluded?

> Answer:

14. Does generated metadata (summaries, descriptions) derived from sensitive content inherit the same handling requirements as the source?

> Answer:

---

## Part 3 — Questions for Infrastructure / Sysadmins

1. What is the storage capacity available to the processing host, and what does it cost to expand?

> Answer:

2. Can a drive be attached to a machine I can reach remotely? What is the approval path?

> Answer:

3. What is the backup and recovery position for working storage during processing?

> Answer:

4. Can we get a second GPU host, or additional L4 capacity, and what is the procurement timeline?

> Answer:

5. What is the network throughput between the storage location and the processing host?

> Answer:

6. Is there an approved path for Gauri to get server access later, and what does she need to have completed first?

> Answer:

7. What monitoring and alerting exists on the processing host? If a multi-day job fails at hour 30, how do I find out?

> Answer:

---

## Part 4 — The hosted-AI question, settled

I want this written down so we stop revisiting it.

These drives contain personal email, unreviewed PII, medical and tax records, and student
records. Sending that content to Copilot, Azure OpenAI, or any hosted API is not something I
think we can justify, and I don't want the architecture to depend on it. The open-source
local-first approach isn't a fallback here — it is the design constraint, and it has the
advantage that it needs no approval and has no per-token cost.

Where AI agents and hosted tools *are* useful is in building the pipeline — helping us write
and debug code, where no archive content is involved. That distinction is worth keeping
sharp, and it's covered in the pipeline design document.

> **Confirm this position with Data Privacy and record the answer:**
>
> **If they say something more permissive, note what it would change:**

---

## Part 5 — Scale reality check

I don't have a good sense of the actual numbers, and everything downstream depends on them.

1. How many drives are queued right now?

> Answer:

2. What is the size range — gigabytes to terabytes?

> Answer:

3. Roughly how many files? A directory listing of one representative drive would answer this
   and the format-mix question at the same time, and it costs nothing to produce even before
   full access is sorted out. **This is the cheapest thing I can ask for and it removes half
   the uncertainty in the throughput model.**

> Answer:

4. What is the expected arrival rate going forward?

> Answer:

5. Is there a prioritisation among the queued drives — collection significance, donor
   deadlines, media degradation risk?

> Answer:

---

## Part 6 — Recommendation

To be completed after the above.

> **Recommended ingest path:**
>
> **Recommended working storage:**
>
> **Recommended delivery layer:**
>
> **What this costs:**
>
> **What it needs approved, and by whom:**
>
> **Fallback if the recommendation is declined:**

---

## Actions log

| Date | Who I asked | Question | Answer | Follow-up |
|---|---|---|---|---|
| | | | | |
