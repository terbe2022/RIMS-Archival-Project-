# Answers from the Archives — August 2026

Record of the responses to `Questions for the Archives` (August 2026).

| | |
|---|---|
| **Asked by** | Tayler Erbe, Data Scientist, AITS |
| **Answered by** | Joanne Kaczmarek, University Archivist |
| **Copied** | Bethany Anderson (Archives) · Brent West (RIMS) |
| **Received** | August 2026, by email with the annotated document attached |
| **Status** | Working record. Superseded only by a later dated version of this file. |

This is the authoritative record of what the Archives has told us. Where a decision in the
scope document or on the board conflicts with something here, **this file wins** and the other
should be corrected.

Answers are reproduced substantively as given. The *"What this changes"* notes are mine and
are engineering interpretation, not the Archives' words — where I have inferred something
rather than been told it, it says so.

**Legend** — ✅ answered · 🟨 partially answered, follow-up needed · ⬜ outstanding

---

## The short version

Six things in this response actually move the build:

1. **There is no single arrival format.** USB stick, laptop, and network transfer are the
   common cases; hard drives, floppies, CDs and DVDs also occur. The source adapter cannot
   assume one shape.
2. **The bottleneck is named, and it is not ingest.** Tracy Popp already does the
   preservation-processing step and lands content on a network drive. Material then waits
   there for archivist appraisal. **That waiting step is the bottleneck, and it is exactly
   what we are building.** This reframes the project: we are not replacing the front of the
   process, we are unblocking the middle of it.
3. **49 collections are already sitting on a network drive** — not on media, not needing to
   be plugged in. Backlog of personal papers only; email and the 12,000 images are separate
   and additional.
4. **The leading numbers are record series numbers, not accession numbers.** RG/series/
   sub-series. This changes the manifest identity design.
5. **BitCurator is already in use; Medusa is the local preservation repository** and is
   itself due for replacement, likely commercial. Preservica and Archivematica are not
   licensed. ePADD has been experimented with only.
6. **Nothing arrives with a hard turnaround obligation, but 3–6 months for personal papers
   and 3 months for administrative records is the target.** No retention schedule forces
   disposal.

**The single most useful sentence in the whole response**, from 1.2 — content already goes
into a network drive space "where the archivists are supposed to review and make final
appraisal decisions. This is our bottleneck." That is the problem statement for this project,
in the Archives' own words.

---

## 1. How material actually reaches the Archives

### ✅ 1.1 — What physically shows up

> An accession can arrive any number of ways: hard drive, laptop, USB stick, network
> transfer, floppy disk, CD, DVD. Most common are USB stick, laptop, or network transfer.

**What this changes.** The source adapter needs at minimum a filesystem-path mode and a
network-location mode. Optical and floppy media are real but rare, and are Tracy's problem
before they are ours — by the time material reaches the stage we operate on, it is already
files on a network drive. We build for **mounted filesystem first**, not for removable media.

---

### ✅ 1.2 — Where the media lives once received — *the key answer in this document*

> Presently we have a person (Tracy Popp) who has responsibility to take content off these
> media formats as we receive them and "process" the content according to best practices of
> digital preservation (descriptive metadata, preservation metadata, administrative metadata,
> file format identification, etc.) and then puts it into a network drive space where the
> archivists are supposed to review and make final appraisal decisions. **This is our
> bottleneck.**

**What this changes — significantly.**

- The physical-media problem is **already solved** and owned by someone else. My assumption
  that we needed a drive plugged into a machine I can reach was solving the wrong problem for
  the backlog. Material is already on a network drive.
- Stage 00 (source & access) shrinks from "get physical drive access" to **"get a mount, a
  share path, and read permission on the Archives network drive."** That is an infrastructure
  and permissions conversation, not a logistics one.
- Some of Stage 01 may be **duplicated work**. Tracy already does format identification and
  produces preservation and administrative metadata. We need to see her output format before
  building our own identify step — we may be able to ingest hers rather than redo it.
- **The bottleneck is appraisal review, which is stages 02 and 06.** That is where the value
  of this project lands. Worth saying explicitly in the next stakeholder update.

**Follow-up needed:** what does Tracy's output look like? What tool produces it, what fields,
what file format, and does it travel with the content onto the network drive?

---

### 🟨 1.3 — Who can connect media to a computer

> I'm not sure we currently have a machine that can be made available to us, but I will talk
> with Tracy Popp about it, as well as our IT team, to see if we can use one of the existing
> computers in IT (or in Tracy's office) for this purpose.

**What this changes.** Lower priority than when asked, given 1.2. What we actually need is
network-drive access, not a machine with a USB port. Re-scope this ask before Joanne spends
capital on it: **ask for read access to the network share instead.**

---

### ✅ 1.4 — How many are waiting

> Right now we have **49 collections** in various levels of organisation, all currently
> living on a network drive. Not sure what media they originally came from. (These are just
> the backlog of documents from "personal papers" — not backlogs of email, or the 12,000
> images previously provided.)

**What this changes.** 49 is a tractable number and a real target. Note carefully what it
excludes: email backlog (unquantified) and the image corpus (12,000, already seen in the
pilot). **We still do not have a size figure — 49 collections could be 50,000 files or
5,000,000.** File count and format mix remain the two unknowns in the throughput model.

**Follow-up needed:** total size on disk of the 49, and a file count. If the network drive is
reachable, `du` and a recursive listing answer both in an afternoon and nobody has to
estimate anything.

---

### ✅ 1.5 — Condition of the media

> This will have been addressed by Tracy Popp when the media was originally brought in.

**What this changes.** Media degradation is out of scope for us. Drop it from risk tracking.

---

### ✅ 1.6 — Forensic imaging

> Some of what we have came from image captures, but not all. Personally I do not think most
> of what we receive needs a bit-for-bit copy including deleted files, for most individuals
> from whom we receive content.

**What this changes.** We do not build a forensic path. Where a disk image already exists in
the backlog we need to be able to read it (E01/raw), because a mounted image looks like a
filesystem — that is a read capability, not an acquisition capability. BitCurator (see 4.1)
covers acquisition if it is ever needed.

---

### 🟨 1.7 — Directory listing of a representative drive

> I can't say we have "one representative drive." If it is from someone copying a laptop or
> workstation, we'll have everything from "My Computer" — 25 or 30 folders, and file counts
> from 100 to 10,000. File types include the typical office ones: .xls, .doc, .pdf, .txt,
> .csv, .mov, .jpg, .mp4, .eml, .pst.

**What this changes.**

- **Per-accession scale is 100 to 10,000 files** — two orders of magnitude, but the top end
  is small. 10,000 files is not a scale problem. 49 collections at, say, 3,000 average is
  ~150,000 files total for the personal-papers backlog. **That is well within reach of a
  single machine.** The throughput model should be rebuilt around this, not around the
  million-file drive I had been designing for.
- **The format list is the extraction routing table, handed to us.** Office documents, plain
  text, CSV, PDF, images, video, and — importantly — `.eml` and `.pst`. Email is not a
  separate lane arriving later; it is inside the personal-papers accessions already.
- `.pst` in the mix means the email work from the pilot is needed in the main line, not
  parked. This is directly relevant to the ePADD decision.
- **Still no actual listing.** The ask stands, and it is now cheaper than before: if we get
  network-drive read access, we generate it ourselves.

---

## 2. Accession numbering

### ✅ 2.1 — Are the leading numbers accession numbers

> The leading numbers are what we call **record series numbers**. This is the primary way we
> keep track of the provenance of the materials. First two digits are the **record group**,
> next two are the **series**, and the last two or three are the **sub-series**. The human-
> readable letters ("FemTech", "MichaelHart") were added to prompt memory of the content.
>
> Reference: [Browse by Campus Unit — University of Illinois Archives](https://archon.library.illinois.edu/archives/index.php?p=collections/classifications)

**What this changes — manifest schema, before v1 is signed off.**

- What we have been calling `accession_id` is a **record series number**, and it identifies
  provenance, not a delivery event. Rename the field. `record_series` is the honest name.
- The structure is parseable: `RG(2) · Series(2) · Subseries(2–3)`. Validation can check
  shape — 6 or 7 digits, and the RG prefix can be checked against the published classification
  list. That gives us the typo-catching we asked for.
- The trailing human-readable label is **not** part of the identifier. Store it as a separate
  `label` column; never parse it, never key on it.
- **A record series number is not unique per delivery.** Two separate deliveries from the same
  office share a number. We therefore need our own delivery-scoped key alongside it —
  something like `record_series + received_date + sequence` — or resuming and re-running
  becomes ambiguous the first time an office sends a second batch.

**Board impact:** this needs to land in the manifest schema before #47 is signed off.

---

### ✅ 2.2 — Format and who assigns

> Assignment is based on where the material came from. In most cases we already have a number
> the materials relate to; sometimes we need to create a new one. Assignment is determined by
> whoever is accessioning the content, with help from colleagues if they are unsure.

**What this changes.** Assignment is human and judgement-based, so the software must never
generate one. Validate shape, check against the published list, flag anything unrecognised
for a person. Do not auto-assign, ever.

---

### ✅ 2.3 — Material with no number yet

> If it does not have a number when we are formally accessioning, I think we need to set it
> aside (not put it into the pipeline) until it has a number.

**What this changes.** Clean and welcome. **A valid record series number is a precondition of
entry.** No holding pen, no provisional identifiers, no reconciliation logic later. The
pipeline refuses unnumbered material at the door and says why.

---

## 3. What counts as worth keeping

### ✅ 3.1 — Short profile per accession

> Yes, it is possible to put together short profiles. In fact, in most cases we shouldn't be
> acquiring content from anonymous people, so having some sort of "bio" info on them makes
> perfect sense.

**What this changes.** Confirmed and agreed. Build the accession-profile input into the
pipeline: a short structured note per accession (person, department, field, active years,
what they worked on), available to enrichment as context. Provide a template rather than
asking for free text — half a page, five fields.

**Follow-up needed:** one profile for one real accession, so the format can be tested against
something real before the template is finalised.

---

### ✅ 3.2 — Always keep

> **Personal papers of most faculty:** correspondence with peers, collaborators, family and
> friends — particularly where it references their research, participation on committees or
> boards, courses taught, articles written, grant applications received, grant reports, books
> written. For some faculty — humanities scholars, English professors for example — drafts of
> final published works are valuable to keep.
>
> **Administrative records from university offices:** Dean or Director communications, annual
> reports from the office, task force reports, meeting minutes and agendas for college or
> school faculty meetings, annual budgets, enrolment statistics, drafts and final versions of
> proposed changes to curricula, courses, goals, etc.

**What this changes — this is the first written appraisal guidance we have.** It is not a
policy, but it is enough to build the first retain rules against.

Two structural points fall out of it:

- **The two accession types have different rules.** Personal papers and administrative records
  need different retain/discard rule sets. The manifest needs an accession-type field, and
  triage needs to branch on it. This was not in the design.
- **Discipline changes the rules.** Drafts are discardable for a scientist and valuable for a
  humanities scholar. This is exactly what the accession profile from 3.1 is for — the profile
  is not just context for a model, it is a **rule selector**.

Correspondence is the single highest-value category and it is also where `.pst` and `.eml`
live. Reinforces that email cannot be a later phase.

---

### ✅ 3.3 — Nearly always safe to set aside

> **Personal papers:** everything related to system operations, including most software
> applications the person loaded onto their computer. Any personal finance information.
> Personally loaded commercial entertainment.
>
> **Administrative records:** accounting details related to general oversight of budget
> expenditures — purchases, payroll records, timesheets. HR-related information such as FMLA
> details, discipline matters, internal personnel discussions (sensitive content).

**What this changes.** Most of this is cheap deterministic filtering, which is the
architecture we already committed to — system files, application binaries and installers, and
known media formats can be removed by path and format alone, before any model is involved.

**One thing here needs care.** HR material, discipline matters and personnel discussions are
described as both *discardable* and *sensitive*. Those are different dispositions and must not
be collapsed. The system should route this material to **restricted review**, not to the
discard pile — the decision to discard sensitive personnel material should be a person's,
recorded, every time. Flag this in the follow-up call.

Personal finance information is a strong PII signal as well as a discard signal, and should
feed both.

---

### ✅ 3.4 — Who provides subject expertise

> Subject expertise is going to be provided by archivists who brought the content in, working
> with subject matter experts as needed.

**What this changes.** The escalation path exists and has a name: the accessioning archivist,
who pulls in an SME when needed. The review queue therefore needs a **per-accession owner**
field, populated at intake, and an escalate action that produces something an outside SME can
look at without Archives system access.

---

### ✅ 3.5 — Anything unexpected ever found

> I'm not aware of that ever happening. But I suppose it COULD happen. It seems like it might
> be some correspondence otherwise assumed to be irrelevant that ended up being insightful
> into a person's research.

**What this changes.** No worked example to design against, but the hypothesis Joanne offers
is a usable one: **correspondence that looks routine but is substantively about the research**.
That is a concrete thing to build a detector for — surface correspondence whose content is
research-adjacent even when the metadata says routine. Worth carrying as a design note for
Stage 04.

---

## 4. Software the University already has

### ✅ 4.1 — What is licensed or running

| Tool | Answer |
|---|---|
| **Preservica** | **No** — the Library built its own, called **Medusa** |
| **Archivematica** | **No** |
| **DROID** | **Unsure** |
| **ePADD** | **Experimented with** |
| **BitCurator** | **Yes** |

**What this changes.**

- **No commercial preservation platform to feed.** The "borrow, don't build" position from
  the questions document still holds, but the thing we borrow is Medusa, which is local and
  in flux (see 5.4).
- **BitCurator is in use** — presumably by Tracy, and presumably where the disk images in 1.6
  came from. It also bundles format identification and PII scanning tooling. Before building
  our own identify and PII steps we should find out which BitCurator components are actually
  in use and what they emit.
- **DROID unsure** is worth resolving because it determines whether our format identifiers
  should match an existing convention. Ask Tracy, not Joanne.
- **ePADD experimented with only** — no institutional commitment, so the ePADD adopt/build
  decision is genuinely open and ours to make. See the email note below, which changes its
  feasibility.

**Board impact:** this answers the open question on the board about which archival software
the University licenses. It can be closed with these findings recorded.

---

### ✅ 4.2 — Who administers them

> I believe it's Tracy Popp.

**What this changes.** **Tracy Popp is the most important person we have not yet spoken to.**
She owns the media processing, the tooling, the metadata output, and the step immediately
upstream of us. A dedicated conversation with her is now a higher priority than most of what
is on the board. Ask Joanne to make the introduction on the follow-up call.

---

### ✅ 4.3 — Existing accessioning procedure to feed

> The current accessioning procedure exists but we've not consistently or effectively followed
> through on it, and it doesn't take us through the point of reviewing the documents.

**What this changes.** Confirms the gap precisely. A procedure exists up to the point where
material lands on the network drive; **there is no procedure past that point**, which is where
the backlog accumulates. We are not competing with an existing workflow — we are extending
one that stops short.

**Follow-up needed:** a copy of the written procedure, so what we build is continuous with it
rather than parallel to it.

---

### ✅ 4.4 — Email tooling

> RIMS is always just supporting the Archives in our endless quest to get an email processing
> procedure in place. They don't really have anything currently in place. The e-discovery tool
> being tested was called **Ringtail**.

**What this changes.** No incumbent email tool to defer to. The pilot email work is not
redundant. Ringtail is e-discovery rather than archival appraisal and is not a candidate for
this. The email lane is ours to design, and per 1.7 it is not optional.

---

## 5. Description and metadata

### ⬜ 5.1 — What standard the output must conform to

> Unsure how to answer this.

**Outstanding, and it is on us, not on Joanne.** The question was too abstract. Rephrase it as
a concrete choice with a recommendation attached and bring it to the call: *"We propose Dublin
Core for descriptive metadata and PREMIS for preservation events, mapped to whatever Medusa
accepts. Does that conflict with anything?"* Easier to react to a proposal than to a blank
field.

Note 5.2 partly answers it in practice: the Archives works in **EAD finding aids at collection
level**, via Archon/ArchivesSpace.

---

### ✅ 5.2 — EAD at collection level, or file-level description

> We work with the finding aids at collection level, but we should already have a collection-
> level description for any collections the digital files belong to.

**What this changes.** Collection-level description already exists — we are not producing it
and should not overwrite it. What we produce is **file-level description that attaches to an
existing collection-level finding aid**. See 5.8, where Joanne raises the same point and asks
the design question directly.

---

### ✅ 5.3 — Mark machine-generated description as such

> Yes.

**What this changes.** Agreed without qualification. Every generated field carries provenance:
what generated it, which model and version, when, and whether a human reviewed it. This is a
manifest schema requirement, not a display convention — it needs columns.

---

### 🟨 5.4 — Is Medusa the destination

> It won't be IDEALS for public findability, but rather the **Library's Digital Library** or
> whatever replaces it. As an aside, we are just about to embark upon a "digital strategies"
> exercise to clarify all the various ways the Library and Archives need and use digital
> systems and content. Part of that is looking at a **replacement for Medusa — likely going to
> a commercial product.**
>
> *(From the summary table: for preservation copies, yes, for now. But for materials that
> won't need restrictions, we will want access copies to display in the Library's Digital
> Library.)*

**What this changes — and it is a real risk.**

- **Two destinations, not one.** Preservation copies to Medusa; access copies to the Digital
  Library for unrestricted material. The pipeline output is a fork, not a single target.
- **IDEALS is out.** Correct my earlier assumption in the scope document.
- **Medusa is being replaced, likely by a commercial product.** Building tightly to Medusa's
  ingest format is building to something with a known expiry. The right response is an
  **export adapter layer**: the pipeline produces a repository-neutral package, and a thin
  adapter maps it to whatever the destination currently is. Costs little now, saves a rebuild.
- **The digital strategies exercise is a stakeholder event we should be inside, not
  downstream of.** A system that appraises and describes born-digital accessions at scale is
  squarely within its scope. Ask Joanne on the call whether we can be represented.

---

### ⬜ 5.5 — Who to talk to about Medusa

> I will check to see who is best to talk to.

Outstanding. Chase on the call. Given 5.4, this should be someone connected to the digital
strategies exercise, not only to Medusa as it stands.

---

### ⬜ 5.6 — Where the working copy lives during processing

> I will find out.

Outstanding, and it stays blocking. This holds full unreviewed accession contents including
unreviewed personal information, so it needs an appropriate location, access control, and a
clearing rule. Related to 5.7, where Joanne has now given us the retention side of it.

---

### ✅ 5.7 — What happens to unselected material

> Which software never deletes? Regardless, once we have COMPLETED the selection stage of
> accessioning, everything else should be deleted. If there is a chance we need more time to
> decide on selection decisions, we will want a clear time period for when that content needs
> to be acted on. This has been one of our challenges — we didn't set such a time period when
> the backlog content was originally brought in.

**What this changes — a correction to our design, and Joanne is right.**

The parenthetical question is fair and I should answer it plainly on the call: *our* software
never deletes on its own. That was a safety property, and I over-applied it. Joanne is asking
for the opposite behaviour at the end of the process: **once selection is complete, everything
not selected should actually be deleted.**

So the design becomes:

- The pipeline never deletes autonomously — unchanged.
- The pipeline **does** provide a deletion action, executed by a person, batched, recorded,
  with an audit trail of who approved what and when.
- **Unselected material gets a clock.** A configurable retention window from the completion of
  selection, after which the system prompts for disposal. Joanne has identified the absence of
  that clock as the root cause of the existing backlog — building it in is directly addressing
  the thing that created the problem.

This is a genuinely useful correction and worth calling out as such.

---

### 🟨 5.8 — An existing finding aid as a model

> Are you imagining a finding aid that provides item-level details, and that the build will be
> able to somehow automatically update existing finding aids? Most of the work in the Archives
> doesn't go to item level in the finding aids. However, the Sousa Archives and Center for
> American Music does. Perhaps we can find a way to incorporate item-level info about digital
> accessions into an existing folder-level-only finding aid?
>
> Example: [John Philip Sousa Music and Personal Papers, circa 1880–1932 — Sousa Archives and Center for American Music](https://archon.library.illinois.edu/archives/index.php?p=collections/controlcard&id=3132&q=sousa)

**What this changes.** Joanne has asked the sharper version of my question back at me, and it
is the right one: **how does item-level machine-generated description attach to a folder-level
human-written finding aid without swamping it?**

That is a genuine design problem and it should be written up as its own decision, not answered
casually. The likely shape: description lives in our own store and the finding aid gains a
link at folder level, rather than item records being pushed into the finding aid itself. This
aligns with what Joanne says in her email about ArchivesSpace links.

The Sousa finding aid is the concrete model to design against — the first example of "good"
we have been given.

---

## 6. Review capacity and oversight

### 🟨 6.1 — Items per week the team could review

> Keeping in mind content comes in irregularly, the weekly item review count and throughput
> could vary greatly. I also don't know what type of review you mean. I've been assuming for
> now you're talking about documents rather than images or email.

**What this changes.** No number yet, and the question was underspecified. Rephrase it as
concrete units on the call rather than asking for a rate:

> *"If the system produced a queue of 200 documents flagged for a decision, each with a
> one-line summary and a suggested disposition — roughly how long would working through that
> take one archivist? An hour? A day? A week?"*

An answer in those terms is what the threshold tuning needs. Also note the assumption to
correct: review will span documents, images **and** email, since per 1.7 `.pst` and `.eml`
arrive inside the same accessions.

---

### ✅ 6.2 — Who reviews flagged sensitive content

> A supervising archivist.

**What this changes.** Distinct role from the accessioning archivist in 3.4. The review queue
needs at least two routes: general appraisal review to the accessioning archivist, sensitive
review to a supervising archivist.

---

### ✅ 6.3 — Proposed oversight thresholds

> **Yes** — the starting position is reasonable, as proposed:

| Situation | Oversight |
|---|---|
| Anything flagged sensitive | Full human review, always |
| Discard decisions, first accession | Full review — treat the first as calibration |
| Discard decisions, later accessions | 5–10% sample, plus everything borderline |
| Auto-selected material | 5–10% audit sample |
| Deleting anything | Explicit approval, in batches, recorded |

**What this changes.** Approved as-is. These are now the configured defaults, not a proposal.
Record them as such in the design and make each one a configurable parameter rather than a
constant.

---

### ✅ 6.4 — Does never-deleting satisfy retention obligations

> There is no schedule that requires actual disposal for these materials. When materials have
> been deposited with the Archives, we are free to delete, return, or keep depending on our
> final appraisal decision and on the terms of a Deed of Gift for personal donations, if one
> exists.

**What this changes.** No externally imposed retention clock. Disposition is governed by
appraisal decision plus Deed of Gift terms where one exists. Combined with 5.7: the constraint
is not legal, it is operational hygiene — and the Deed of Gift is a per-accession input the
manifest may need to carry a reference to.

---

### ✅ 6.5 — Who authorises deletion

> The archivist responsible for the accession.

**What this changes.** Confirms the per-accession owner field from 3.4 and gives it a second
job: deletion authority. One field, two uses.

---

## 7. Restrictions and access

### 🟨 7.1 — Donor agreements and estate restrictions

> I'm not sure I agree, but it also might just be that I don't understand. We have central
> storage (in duplicate) for the Deeds of Gift within the Library. The U of I Foundation also
> keeps track of them, along with all the other types of donor agreements for the University.

**What this changes.** My question was unclear, not Joanne's answer. I was not proposing to
store Deeds of Gift in the pipeline — I was asking whether the *restrictions they impose*
should travel with the files so nobody has to remember them.

Rephrase for the call: *"The Deeds of Gift stay where they are. What I'm asking is whether the
manifest should carry a pointer — 'this accession has a Deed of Gift, here is its reference,
here are the restrictions it imposes' — so the system can enforce them automatically rather
than depending on someone recalling them."*

---

### ✅ 7.2 — Litigation hold or open FOIA

> Nothing in the Archives queue is under litigation hold or open FOIA request.

**What this changes.** Clean for the current backlog. The pipeline should still carry a hold
flag that freezes an accession, because this is a point-in-time answer — but it is not
blocking anything now.

---

### ✅ 7.3 — Access levels

> We use **"open"** and **"restricted."**

**What this changes.** Two values, not three or more. The access field is a two-state
enumeration using the Archives' own vocabulary. Do not invent finer gradations.

---

### ⬜ 7.4 — Where the PII mapping store lives *(directed to Brent)*

> *(No answer — this question was addressed to Brent West.)*

**Outstanding and blocking for Stage 04.** Follow up with Brent directly rather than routing
through Joanne. The question stands: where does the mapping between redacted placeholders and
real values live, who can read it, and does it need encryption at rest.

**Board impact:** the board item on where the PII mapping store lives stays blocked, and the
blocker should be re-labelled to Brent.

---

### ✅ 7.5 — Who may see unredacted content during processing

> I would like both Gauri and you to have permissions to see unredacted content during
> processing. **Is there any sort of template for an NDA that AITS has everyone sign that we
> can model here in the Archives?** Presently we are not very tight about that sort of
> control.

**What this changes.** Cleared for both of us. Joanne has also asked a question back, and it
deserves a real answer rather than a shrug — she is asking us to help formalise something the
Archives currently does informally, which is a reasonable ask and cheap goodwill.

**Action:** find out what AITS uses for confidentiality agreements and whether it can be
adapted. Route via Brent, who will know the RIMS-side answer.

---

## 8. Scope and expectations

### ✅ 8.1 — What success looks like

> Two measures of success: first, getting through the backlog of digital content (volume
> processed). But long-term, making it easy for researchers to have access to the digital
> content **and** be able to easily find things would be the primary goal.

**What this changes.** Two objectives with an explicit ordering: **backlog throughput now,
discoverability as the long-term primary goal.** That ordering is the answer to the
optimisation question I asked — it means Stage 06 (index, search and delivery) is not a
trailing nice-to-have, it is where the durable value is. Do not let it slide to the end and
get cut.

---

### ✅ 8.2 — Acceptable turnaround per accession

> With no backlog, for personal papers from faculty and sometimes alumni: **3 to 6 months**
> from receipt. For administrative records (Chancellor's Files, President's Office Files):
> **no more than 3 months.**

**What this changes.** Generous relative to what the pipeline can do, which means **we should
not optimise for speed.** Trade throughput for accuracy and for more human checking wherever
the choice arises. It also confirms the accession-type split from 3.2 — the two types have
different rules *and* different service levels.

---

### 🟨 8.3 — Prioritisation among queued accessions

> No current priority list, but I can make one.

**What this changes.** Take her up on it, but make it easy: rather than asking for a ranked
list of 49, ask which **three or four** should go first and why. The reasons matter more than
the ranking — they tell us what the Archives values, which feeds triage.

---

### ✅ 8.4 — Do the accessions span specialist disciplines

> Yes.

**What this changes.** Confirmed but unelaborated. Combined with 1.7, the format list is
office-typical, so specialist formats are the tail rather than the body. Handle the common
formats first; treat specialist formats as a routing exception that flags for human attention
rather than failing.

---

## Notes from the covering email

Joanne's email raised three things that are not in the document and that matter as much as
several of the answers.

### Access model may differ by material type

> I think that might vary based on whether we're talking about email or the documents we
> receive from faculty. I am wondering about having a stand-alone workstation in the Archives
> for accessing the email — but not sure about searchable index vs a web browsing option.

**Implication.** Access is not one design. Email may warrant a restricted, physically-located
access model — a reading-room workstation — while documents get linked from the catalogue.
That distinction should be made explicitly in Stage 06 rather than assumed away. The
searchable-index-versus-browse question is a real design fork and worth its own decision.

### ePADD may be blocked by Library IT

> I have asked if Library IT will allow us to have ePADD installed on a workstation here in
> the Archives so we can also get familiar with it, but haven't heard back yet. They have some
> concerns with vulnerabilities associated with Java Runtime.

**Implication — this materially affects the ePADD decision.** If Library IT will not permit a
Java runtime on Archives workstations, ePADD is not adoptable regardless of how well it
performs in evaluation. The evaluation should continue, but **the deployment question needs
answering in parallel, and it may decide the matter before the evaluation does.**

This is worth recording as a real finding: the adopt-or-build decision on email may be settled
by an IT security constraint rather than by capability.

### ArchivesSpace is the access layer, with links out to storage

> For documents coming in as part of a donation of personal papers, it would be nice to have
> links in **ArchivesSpace** (our soon-to-be archives searchable database) that could take you
> directly to the digital files, which would be stored elsewhere — not in ArchivesSpace —
> either directly in the Medusa preservation repository or in the Library's Digital Library.

**Implication — this is the missing piece of the delivery architecture.**

```
ArchivesSpace  →  finding aids and description, with links out
       │
       ├──→  Medusa (or its replacement)   preservation copies
       └──→  Library Digital Library       access copies, unrestricted material
```

ArchivesSpace is being adopted ("soon-to-be"), which means **there is a window to influence
how digital accession description enters it, and that window is open now.** It also answers
5.8 in practice: item-level description does not go *into* the finding aid, it is *linked
from* it. And it confirms the two-destination fork from 5.4.

Add ArchivesSpace to the systems we design against. It was not previously on the list.

---

## Still outstanding

| # | Question | Owner | Status |
|---|---|---|---|
| 1.3 | A machine for connecting media | Joanne → Tracy / IT | Re-scope: ask for network-drive read access instead |
| 1.4a | Total size and file count of the 49 collections | Joanne / Tracy | New — follows from 1.4 |
| 1.7 | A real directory listing | Joanne / Tracy | Still open; trivial once we have drive access |
| 5.1 | Metadata standard the output must conform to | Tayler → Joanne | Rephrase as a proposal to react to |
| 5.5 | Who to talk to about Medusa | Joanne | "I will check" |
| 5.6 | Where the working copy lives | Joanne | "I will find out" — still blocking |
| 7.1 | Whether restrictions should travel in the manifest | Tayler → Joanne | Rephrase; my question was unclear |
| 7.4 | PII mapping store location and controls | **Brent** | Never answered — chase directly |
| 6.1 | Review capacity, in concrete units | Joanne | Rephrase as "how long would 200 items take" |
| 8.3 | Which three or four accessions go first | Joanne | Offered — take her up on it |
| — | Tracy Popp's output format and tooling | Joanne → Tracy | **New, and high value** |
| — | Copy of the written accessioning procedure | Joanne | New, from 4.3 |
| — | Does the Library run DROID | Tracy | From 4.1 |
| — | ePADD deployment permission from Library IT | Joanne → Library IT | From the email — may decide the email lane |
| — | AITS confidentiality agreement template | Tayler → Brent | Joanne asked us for this |
| — | Can we be represented in the digital strategies exercise | Joanne | From 5.4 |

---

## What this changes on the board

| Item | Effect |
|---|---|
| Which archival software the University already licenses | **Answerable and closeable** — 4.1 gives the full table |
| Meeting with Joanne — accessions, numbering, standards, capacity | Largely answered; remaining items become the follow-up call agenda |
| Appraisal policy and a labelled sample | **Partly unblocked** — 3.2 and 3.3 are the first written guidance. The labelled sample is still outstanding |
| Manifest schema v1 — review and sign off | **Do not sign off yet.** Needs the record-series rename, the accession-type field, the generated-field provenance columns, and a delivery-scoped key |
| Decide where the PII mapping store lives | Stays blocked; re-label the blocker to Brent, not Joanne |
| Stage 00 — source & access | Re-scope from physical drives to network-drive access |
| Stage 01 — inventory & identify | Check against Tracy's existing output before building; may be partly redundant |
| Stage 02 — triage & appraisal | Needs to branch on accession type. First retain/discard rules can be drafted from 3.2 and 3.3 |
| Stage 03 — extraction routing table | Format list from 1.7 is the starting routing table, `.pst` and `.eml` included |
| Stage 06 — index, search & delivery | Promoted in importance by 8.1. Add ArchivesSpace, and the two-destination fork |
| Decide: adopt ePADD, or keep our own lane | New constraint — Library IT may block the Java runtime entirely |
| Throughput model and drive sizing calculator | Rebuild around 100–10,000 files per accession, ~49 accessions, not million-file drives |
| **New** | Talk to Tracy Popp — tooling, output format, and the upstream handoff |
| **New** | Design decision: how item-level description attaches to folder-level finding aids |
| **New** | Design decision: repository-neutral export with an adapter layer, given Medusa's replacement |

---

## Agenda for the follow-up call

1. Confirm the reframing — the bottleneck is appraisal review, and that is what we are
   building. Everything upstream is already Tracy's.
2. Ask for network-drive read access instead of a machine for plugging in media.
3. Ask for an introduction to Tracy Popp.
4. Answer 5.7 directly: our software does not delete on its own, but it will provide a
   recorded, batched deletion action — and a retention clock, which is the thing that was
   missing when the backlog formed.
5. Re-ask 6.1 in concrete terms: how long would a queue of 200 flagged documents take.
6. Re-ask 7.1 in concrete terms: a pointer and restrictions in the manifest, not the Deed of
   Gift itself.
7. Raise 5.1 as a proposal — Dublin Core plus PREMIS, mapped to the destination — rather than
   as an open question.
8. Flag the HR/personnel point from 3.3: discardable and sensitive are different dispositions
   and should not be collapsed.
9. Ask about representation in the digital strategies exercise, given Medusa's replacement.
10. Take up the offer in 8.3 — which three or four accessions first, and why.
11. Confirm we will come back on the confidentiality-agreement question from 7.5.

---

*Recorded from the annotated document and covering email received August 2026. Engineering
interpretation is mine and open to correction by the Archives.*
