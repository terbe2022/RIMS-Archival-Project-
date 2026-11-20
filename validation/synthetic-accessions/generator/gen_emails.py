"""Email lane: loose .eml files, an mbox export, attachments, forwarded chains."""
from __future__ import annotations

import io
import mailbox
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from datetime import datetime, timezone, timedelta

from common import reg, PEOPLE, ROOT_NAME

CST = timezone(timedelta(hours=-6))
CDT = timezone(timedelta(hours=-5))


def addr(key):
    n, e = PEOPLE[key]
    return f"{n} <{e}>"


def build(sender, to, subject, body, date, cc=(), html=None, attachments=(),
          charset="utf-8", in_reply_to=None, extra_headers=None):
    m = EmailMessage()
    m["From"] = addr(sender) if sender in PEOPLE else sender
    m["To"] = ", ".join(addr(t) if t in PEOPLE else t for t in to)
    if cc:
        m["Cc"] = ", ".join(addr(c) if c in PEOPLE else c for c in cc)
    m["Subject"] = subject
    m["Date"] = format_datetime(date)
    m["Message-ID"] = make_msgid(domain="mail.illinois.example.edu")
    if in_reply_to:
        m["In-Reply-To"] = in_reply_to
    for k, v in (extra_headers or {}).items():
        m[k] = v
    if body is not None:
        m.set_content(body, charset=charset)
    if html:
        if body is None:
            m.set_content(html, subtype="html")
        else:
            m.add_alternative(html, subtype="html")
    for fname, data, maintype, subtype in attachments:
        m.add_attachment(data, maintype=maintype, subtype=subtype, filename=fname)
    return m


def d(y, mo, day, h=9, mi=0, tz=CDT):
    return datetime(y, mo, day, h, mi, tzinfo=tz)


# --------------------------------------------------------------------------
# Attachment payloads built in-memory (small, real formats)
# --------------------------------------------------------------------------
def tiny_csv():
    rows = ["site,date,trap_color,bee_count,notes",
            "SBP,2019-06-14,blue,23,windy afternoon",
            "SBP,2019-06-14,yellow,17,",
            "SBP,2019-06-14,white,9,one bowl tipped",
            "BRF,2019-06-15,blue,31,B. affinis worker netted 10:40",
            "BRF,2019-06-15,yellow,22,",
            "BRF,2019-06-15,white,12,"]
    return ("\n".join(rows) + "\n").encode()


def tiny_png(text, size=(480, 300), bg=(245, 240, 225)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", size, bg)
    dr = ImageDraw.Draw(im)
    for i in range(0, size[0], 40):
        dr.line([(i, size[1]), (i + 20, size[1] - 120 - (i % 70))], fill=(90, 130, 60), width=3)
    dr.ellipse([200, 90, 260, 130], fill=(230, 180, 40), outline=(40, 30, 10), width=3)
    dr.line([(210, 95), (210, 125)], fill=(40, 30, 10), width=6)
    dr.line([(232, 92), (232, 128)], fill=(40, 30, 10), width=6)
    dr.text((10, 10), text, fill=(30, 30, 30))
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def tiny_docx(title, paras):
    import docx
    doc = docx.Document()
    doc.add_heading(title, 1)
    for p in paras:
        doc.add_paragraph(p)
    b = io.BytesIO()
    doc.save(b)
    return b.getvalue()


def ics(summary, start, end, location, desc):
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Synthetic//Archivist Test//EN\r\n"
        "METHOD:REQUEST\r\nBEGIN:VEVENT\r\n"
        f"UID:{abs(hash(summary))}@illinois.example.edu\r\n"
        f"DTSTART:{start}\r\nDTEND:{end}\r\nSUMMARY:{summary}\r\n"
        f"LOCATION:{location}\r\nDESCRIPTION:{desc}\r\n"
        "END:VEVENT\r\nEND:VCALENDAR\r\n").encode()


# --------------------------------------------------------------------------
# Message definitions
# --------------------------------------------------------------------------
# Each: dict(msg=EmailMessage, rel, why, sens, title, summary, kw, diff, tags)
def messages():
    M = []

    def add(msg, rel, why, title, summary, kw, sens=("none",), diff="obvious", tags=()):
        M.append(dict(msg=msg, rel=rel, why=why, sens=sens, title=title, summary=summary,
                      kw=kw, diff=diff, tags=list(tags)))

    # ---------------- HIGH: methods, findings, collaborators ----------------
    add(build("quintero", ["achterberg"], "Re: richness plateau - mixed model results",
        """Miriam,

I reran the richness models with site as a random intercept and restoration age as
a smoothed term (k = 5) rather than the linear fit we had in the March draft. The
result is cleaner than I expected:

  * Rarefied species richness rises steeply for the first 6-8 years and is flat
    after about year 10 (edf = 2.7, p < 0.001).
  * The ground-nesting specialists (Andrena, Calliopsis, the Melissodes we can
    resolve to species) do NOT plateau. They are still climbing at 25 years, and
    the two oldest restorations (SBP, KRR) are still below the Ritter remnant.
  * Pan-trap colour interacts with year, but it does not change the shape of the
    curve, so I think we can report blue/yellow/white pooled and put the colour
    model in the supplement.

The uncomfortable part: if we drop BRF (the remnant) the specialist result loses
most of its power, because the remnant anchors the top end. Reviewers will ask
about that. I'd rather we say it up front than have it pulled out of us.

Code is in the shared folder under analysis/gam_richness_v4.R. I fixed the
offset for unequal trapping effort (we were using bowl-days without removing
tipped bowls).

Rafael
""", d(2020, 4, 22, 16, 41)),
        "high", "Correspondence with collaborators that discusses methods and findings",
        "Quintero reports mixed-model results on bee richness plateau",
        "Statistician Rafael Quintero reports that native bee richness plateaus about 10 years after restoration while ground-nesting specialists keep increasing; notes dependence on the Ritter remnant site and a corrected trapping-effort offset.",
        ["species richness", "GAM", "restoration age", "ground-nesting bees", "Ritter remnant"])

    add(build("achterberg", ["quintero"], "Re: Re: richness plateau - mixed model results",
        """Rafael -- agreed, say it up front. I'll write a paragraph for the
discussion framing BRF as the reference condition rather than a data point, and we
can show the specialist curve with and without it in Fig. S4.

I also want to check whether the specialist lag tracks bare-ground cover. Jonah's
2019 quadrat data have percent bare ground at every pan-trap station. If ground
nesters are limited by nesting substrate rather than flowers, that's a management
recommendation DNR can actually act on (prescribed burns open up bare ground).

-- M

On Wed, Apr 22, 2020 at 4:41 PM Rafael Quintero wrote:
> I reran the richness models with site as a random intercept ...
""", d(2020, 4, 23, 7, 12)),
        "high", "Correspondence with collaborators that discusses methods and findings",
        "Achterberg proposes testing bare-ground cover as driver of specialist lag",
        "Reply agreeing to present the remnant site as a reference condition and proposing to test whether ground-nesting bee recovery is limited by bare-ground nesting habitat, with a management implication for prescribed burning.",
        ["bare ground", "nesting habitat", "prescribed burn", "supplementary figure"])

    add(build("natarajan", ["achterberg"], "B. affinis at BRF again -- photos attached",
        """Hi Miriam,

Netted another rusty patched worker at the Ritter remnant this morning, 10:40,
on Monarda fistulosa along the north fence line, same patch as last July. I
photographed her in the vial and released her (permit conditions). Photos
attached. Air temp 24 C, wind light, sunny.

GPS for the patch is in the field tablet (waypoint BRF-07). I did NOT put it in
the shared spreadsheet given what Karen said about the location layer.

Harold came out to talk while I was there. He's asking if he can tell the
neighbour who is thinking of spraying soybeans next to the fence. I said I'd ask
you before he says anything about the bee specifically.

Priya
""", d(2019, 6, 15, 14, 5), attachments=[("BRF_affinis_vial_2019-06-15.png",
        tiny_png("B. affinis worker in vial - BRF 2019-06-15"), "image", "png")]),
        "high", "Correspondence with students that discusses findings and site access; specimen photograph",
        "Rusty patched bumble bee netted again at Ritter remnant",
        "Graduate student reports a second record of the endangered rusty patched bumble bee at the Ritter Farm Remnant, attaches a vial photograph, withholds GPS from the shared spreadsheet, and relays the landowner's question about a neighbour's pesticide spraying.",
        ["Bombus affinis", "endangered species", "Ritter Farm", "Monarda fistulosa", "landowner"],
        sens=("sensitive_location",), tags=["email_with_attachment"])

    add(build("lindqvist", ["achterberg"], "Location data for Bombus affinis records -- please read",
        """Dr. Achterberg,

Thank you for reporting the June 2019 rusty patched bumble bee observations from
Ford County. These are the first confirmed records in that county since 2008.

Because B. affinis is federally listed, the Department asks that exact
coordinates not be published, shared in data repositories, or included in
presentations. Please generalise to county or to a 10 km grid cell in anything
public, and submit exact locations only through the Natural Heritage Database
portal. The landowner's identity should also be kept out of public materials.

I'd also like to talk about whether the Ritters would consider a voluntary
conservation agreement. Could we meet in July?

Karen Lindqvist
Natural Areas Program, Illinois DNR (synthetic)
""", d(2019, 6, 20, 11, 30)),
        "high", "Correspondence with Illinois DNR staff that discusses conservation decisions",
        "IDNR guidance on withholding rusty patched bumble bee locations",
        "Illinois DNR asks that exact coordinates of the federally listed rusty patched bumble bee and the landowner's identity be withheld from publications and repositories, and proposes discussing a conservation agreement with the landowners.",
        ["Illinois DNR", "data sharing", "endangered species", "location privacy", "conservation agreement"],
        sens=("sensitive_location",))

    add(build("editor", ["achterberg"], "Decision on JPE-2020-0388: Major revision",
        """Dear Dr. Achterberg,

Manuscript JPE-2020-0388, "Native bee richness recovers within a decade of
prairie restoration, but ground-nesting specialists lag", has been reviewed. The
reviewers find the dataset unusually strong and the question important, and I
am pleased to invite a major revision.

Reviewer 1 is concerned that the specialist result depends on a single remnant
site and asks for a sensitivity analysis excluding it. Reviewer 2 asks for the
trapping-effort correction to be described in the main text and questions
whether floral resource density was controlled for. Reviewer 3 asks that the
data be deposited with location precision appropriate for listed species.

Please submit your revision within 90 days with a point-by-point response.

Sincerely,
Handling Editor, Journal of Pollination Ecology (synthetic)

--- Reviewer comments are attached as JPE-2020-0388_reviews.txt ---
""", d(2020, 9, 2, 8, 15), attachments=[("JPE-2020-0388_reviews.txt",
        b"Reviewer 1: The specialist-lag conclusion rests heavily on site BRF...\n"
        b"Reviewer 2: Please describe the bowl-day offset in Methods...\n"
        b"Reviewer 3: Data deposit should generalise B. affinis locations...\n", "text", "plain")]),
        "high", "Reviewer correspondence that shows how the papers changed",
        "Journal decision: major revision for bee richness manuscript",
        "Editor's major-revision decision on the restoration-age manuscript summarising three reviewers' requests: a sensitivity analysis without the remnant site, a description of the trapping-effort correction and floral density, and location-generalised data deposit.",
        ["peer review", "major revision", "Journal of Pollination Ecology", "manuscript"],
        tags=["email_with_attachment"])

    add(build("feld", ["achterberg"], "pan trap protocol v3 + question about tipped bowls",
        """Hi Dr. A,

Attached is the updated pan trap protocol (v3). Changes from v2:
 - bowls set by 08:30 and collected after 24 h (was 'same day')
 - tipped or flooded bowls recorded as 0 effort, not 0 bees
 - soapy water: 3 drops Dawn Ultra per litre (we ran out of the blue Dawn)
 - photos of each transect at set-up, facing north

Question: for 2017 we didn't record tipped bowls separately. Should I code those
seasons as 'effort unknown' or assume full effort? Rafael says unknown.

Jonah
""", d(2019, 5, 2, 21, 48), attachments=[("PanTrap_Protocol_v3.docx", tiny_docx(
        "Pan Trap Protocol v3", ["Set 15 bowls per station (5 blue, 5 yellow, 5 white) at 1 m spacing.",
                                 "Collect after 24 hours; record tipped or flooded bowls as zero effort.",
                                 "Transfer specimens to 70% ethanol; label with site, station, date, colour."]),
        "application", "vnd.openxmlformats-officedocument.wordprocessingml.document")]),
        "high", "Correspondence with students that discusses methods; field protocol",
        "Pan trap protocol version 3 and handling of tipped bowls",
        "Graduate student sends version 3 of the pan-trap field protocol (24-hour sets, tipped bowls as zero effort) and asks how to code 2017 seasons where tipped bowls were not recorded.",
        ["pan trap", "protocol", "sampling effort", "field methods"],
        tags=["email_with_attachment"])

    add(build("ritter", ["achterberg"], "the old prairie on our place",
        """Dear Miriam,

June and I enjoyed having your students out. You asked about the history of the
north pasture. My grandfather bought the place in 1911 and the north forty was
never broke because it was too wet to plow with horses. Dad ran a few cows on it
in the 40s and 50s but quit when he went to row crops. We have burned it every
few years since about 1975 because June's father said that's what kept it in
flowers.

I don't want the bee business to mean the government tells us what to do with
the rest of the farm. But we would like to know what's out there. Is it all
right if I tell Dale next door to hold off spraying near the fence in July?

Harold Ritter
Ford County
(555) 0142
""", d(2019, 6, 18, 19, 2, CDT)),
        "high", "Correspondence with landowners that discusses site history and conservation decisions",
        "Landowner Harold Ritter on the history of the remnant prairie",
        "Landowner describes the Ritter Farm north pasture as never plowed since 1911, lightly grazed mid-century and periodically burned since 1975, voices concern about regulation, and asks whether to warn a neighbour about spraying.",
        ["land history", "remnant prairie", "prescribed fire", "landowner", "Ford County"],
        sens=("pii_contact", "sensitive_location"), diff="subtle")

    # Forwarded chain: tests thread decomposition (POC 1 strength)
    chain = """Forwarding the whole thread so you have the history before Thursday's call.
-- Celine

-----Original Message-----
From: Karen Lindqvist
Sent: Monday, March 2, 2020 9:14 AM
To: Celine Baptiste
Subject: RE: Prairie Bee Survey - statewide working group

Celine, yes, IDNR would support Miriam presenting the chronosequence results to
the working group, provided the BRF records are shown at county level only.

-----Original Message-----
From: Celine Baptiste
Sent: Friday, February 28, 2020 4:50 PM
To: Karen Lindqvist
Subject: Prairie Bee Survey - statewide working group

Karen, the Illinois Pollinator Working Group would like a talk on the
restoration-age results at the April meeting. The draft management guidance
we are writing currently assumes ten years is enough for bees. Miriam's
specialist result suggests otherwise. Can IDNR live with that being discussed?

-----Original Message-----
From: Miriam Achterberg
Sent: Thursday, February 27, 2020 10:02 PM
To: Celine Baptiste
Subject: guidance draft section 4

Celine, section 4 of the guidance says 'pollinator communities typically
recover within 5-10 years.' That is true for total richness and wrong for
ground-nesting specialists in our data. I'd suggest '...total richness recovers
within 5-10 years, but specialist and ground-nesting species may require
decades and benefit from management that maintains bare ground.'
"""
    add(build("baptiste", ["achterberg"], "FW: Prairie Bee Survey - statewide working group", chain,
              d(2020, 3, 3, 8, 2)),
        "high", "Correspondence that discusses findings and conservation decisions",
        "Forwarded thread on statewide pollinator guidance and survey results",
        "Forwarded three-message chain in which Achterberg asks the Illinois Pollinator Working Group to revise guidance claiming bees recover in 5-10 years, the group invites a talk, and IDNR agrees provided the BRF records are generalised.",
        ["pollinator guidance", "working group", "forwarded thread", "management recommendations"],
        diff="subtle", tags=["email_thread_forwarded"])

    # ---------------- MODERATE ----------------
    add(build("reporter", ["achterberg"], "Interview request: bees and prairie restoration",
        """Hi Professor Achterberg,

I'm writing a piece for the Sunday Courier on the prairie plantings going in
along Lafayette Road and whether they actually help pollinators. A colleague
pointed me to your work. Could I call you for 20 minutes this week? I'd also
love to send a photographer out with your field crew if that's possible.

Lena Ortiz, Champaign Courier (synthetic)
""", d(2021, 7, 12, 10, 3)),
        "moderate", "Records documenting her career and outreach; does not itself discuss findings",
        "Newspaper interview request about prairie plantings and pollinators",
        "A local reporter requests an interview and a photo visit with the field crew for a story on whether roadside prairie plantings help pollinators.",
        ["media", "outreach", "interview request"], diff="subtle")

    add(build("achterberg", ["natarajan"], "Re: committee meeting + chapter 2 comments",
        """Priya,

Chapter 2 is in good shape. My main comments: (1) the floral-resource index
needs a sentence justifying the use of Monarda and Pycnanthemum as the
indicator taxa; (2) Fig 2.3 should share a y-axis with Fig 2.2 so readers can
compare; (3) move the barcoding failures table to an appendix.

Let's hold the committee meeting the week of Nov 9. Please send a poll.

M.
""", d(2020, 10, 19, 15, 30)),
        "high", "Supervised dissertation chapter drafts and correspondence discussing methods",
        "Comments on Natarajan dissertation chapter 2",
        "Achterberg returns comments on a supervised dissertation chapter about floral resource indices and figure layout, and asks the student to schedule a committee meeting.",
        ["dissertation", "chapter draft", "floral resources", "advising"], diff="subtle")

    add(build("deptadmin", ["achterberg"], "Your seminar is confirmed: Oct 14, 3:00 pm",
        """Dear Professor Achterberg,

This confirms your departmental seminar, "Thirty years of prairie restoration
through the eyes of a bee," on Wednesday, October 14 at 3:00 pm in Room 101
(synthetic building). A calendar invitation is attached. Please send slides to
the office by noon on the day so we can load them on the podium computer.
""", d(2020, 10, 1, 9, 0), attachments=[("seminar.ics", ics(
        "Achterberg seminar: Thirty years of prairie restoration", "20201014T200000Z",
        "20201014T210000Z", "Room 101", "Departmental seminar"), "text", "calendar")]),
        "moderate", "Talks presenting the research (logistics only, not the talk itself)",
        "Seminar confirmation with calendar invitation",
        "Department office confirms Achterberg's seminar on prairie restoration and bees and attaches an iCalendar invitation.",
        ["seminar", "calendar", "talk"], diff="subtle", tags=["calendar_attachment"])

    add(build("baptiste", ["achterberg"], "Newsletter: Pollinator Partners Quarterly - Spring 2021",
        None, d(2021, 4, 2, 6, 0), html="""<html><body>
<h1>Pollinator Partners Quarterly</h1><p>In this issue: native plant sales across the
Midwest, a profile of Prof. Miriam Achterberg's prairie bee research, and how to
build a bee hotel.</p><p>Read the profile: <a href="https://partners.example.org/achterberg">here</a></p>
<p style="font-size:10px">You are receiving this because you subscribed. Unsubscribe.</p></body></html>"""),
        "low", "Newsletters she only subscribed to (excluded), though this issue profiles her work",
        "Pollinator newsletter issue profiling Achterberg's research",
        "Subscription newsletter (HTML only) whose spring issue includes a profile of Achterberg's prairie bee research alongside general gardening content.",
        ["newsletter", "profile", "outreach"], diff="ambiguous", tags=["html_only"])

    # ---------------- LOW ----------------
    add(build("deptadmin", ["achterberg"], "Parking lot E14 closed for resurfacing July 6-10",
        """All faculty and staff,

Lot E14 will be closed July 6-10 for resurfacing. Permit holders may park in
E15 or the Fourth Street garage during this period. Please remove vehicles by
6:00 am on July 6.

Facilities and Services (synthetic)
""", d(2020, 6, 29, 13, 0)),
        "none", "Routine building notices and parking messages she did not write",
        "Parking lot closure notice",
        "Facilities notice that a staff parking lot will be closed for resurfacing.",
        ["parking", "facilities"])

    add(build("it", ["achterberg"], "Action required: Duo enrollment by Friday",
        """Your account requires two-factor enrollment by Friday. Visit the help desk
portal to enroll. This is an automated message.""", d(2018, 2, 12, 8, 0)),
        "none", "Routine IT messages",
        "IT two-factor enrollment reminder",
        "Automated campus IT reminder to enroll in two-factor authentication.",
        ["IT", "two-factor"])

    add(build("deptadmin", ["achterberg"], "Travel confirmation: ESA Annual Meeting, St. Louis",
        """Your travel is booked.
Flight: none (driving). Hotel: Riverfront Inn (synthetic), Nov 17-20, conf # 88412.
Registration: Entomological Society annual meeting, paid on department card.
Please keep receipts for reimbursement.""", d(2019, 10, 3, 11, 20)),
        "low", "Travel booking confirmations (routine administration); shows conference attendance",
        "Travel confirmation for entomology annual meeting",
        "Booking confirmation for hotel and registration at an entomology annual meeting, with a reminder to keep receipts.",
        ["travel", "conference", "reimbursement"], diff="subtle")

    add(build("vendor", ["achterberg"], "40% OFF insect pins + FREE shipping this week only!!",
        None, d(2021, 3, 15, 5, 30), html="""<html><body style="background:#ffd">
<h1>SPRING SALE</h1><p>Stainless insect pins, unit trays, Schmitt boxes - 40% off!</p>
<p><a href="http://bugsupply.example.com/sale?id=88">SHOP NOW</a></p></body></html>"""),
        "none", "Vendor marketing",
        "Entomology supply vendor sale advertisement",
        "HTML marketing email from an entomology equipment vendor advertising discounts on insect pins and storage boxes.",
        ["marketing", "vendor", "spam"], diff="subtle", tags=["html_only"])

    add(build("Payroll Services <payroll-update@illinois-edu.example.net>", ["achterberg"],
        "URGENT: Verify your direct deposit to avoid payment delay",
        """Dear Employee,

Due to a system upgrade, all staff must re-verify direct deposit information
within 24 hours. Click the secure link below and sign in with your NetID and
password.

http://illinois-edu.example.net/verify

Payroll Department""", d(2022, 1, 7, 2, 14)),
        "none", "Spam and phishing messages",
        "Phishing message impersonating payroll",
        "Phishing email from a look-alike domain urging the recipient to re-enter NetID credentials to verify direct deposit.",
        ["phishing", "spam", "security"], tags=["phishing"])

    # ---------------- SENSITIVE / mixed ----------------
    add(build("achterberg", ["okonkwo"], "Confidential: Doug Penner - performance concerns",
        """Adaeze,

I need advice on how to handle Doug. Since March he has missed four field days
without notice, and on May 30 the -80 freezer alarm went unanswered over the
weekend; we lost about 300 DNA extracts from the 2018 season. I've talked with
him twice informally. He mentioned personal issues at home and I don't want to
pry, but I think we need a written performance improvement plan.

Can HR join us next week? Please keep this between us for now.

Miriam""", d(2019, 6, 4, 18, 22)),
        "low", "Personnel matters concerning lab staff must be restricted; loss of 2018 extracts is a minor research fact",
        "Confidential personnel concern about lab technician",
        "Achterberg asks the department head for help with a lab technician's attendance and a freezer failure that destroyed about 300 DNA extracts, and proposes a performance improvement plan.",
        ["personnel", "performance", "freezer failure", "DNA extracts"],
        sens=("hr_personnel",), diff="ambiguous")

    add(build("tom", ["achterberg"], "mom's appointment + groceries",
        """Hey - Mom's cardiology appointment got moved to Thursday at 2. Can you
take her? I've got the school pickup. Also we're out of coffee and dog food.

Love, T""", d(2021, 2, 9, 12, 33)),
        "none", "Personal and household records unrelated to university work",
        "Family message about appointment and groceries",
        "Personal message from her spouse about a relative's medical appointment and household shopping.",
        ["personal", "family"], sens=("medical",))

    add(build("feld", ["achterberg"], "Re: grad application - letter for Jonah?",
        """Thanks for agreeing to write. My PhD applications are due Dec 1. Programs:
Prairie State (Quintero lab), Cornell-like U (synthetic), and Wisconsin-like
U (synthetic). My GPA is 3.71 and GRE wasn't required. I attached my CV and
statement of purpose.""", d(2020, 11, 2, 9, 45)),
        "low", "Student records and letters about students are FERPA-protected",
        "Student request for recommendation letter",
        "Master's student asks for recommendation letters for PhD applications and shares GPA and application materials.",
        ["recommendation letter", "graduate admissions", "student"], sens=("ferpa_student",),
        diff="subtle")

    # Legacy charset message (Latin-1)
    add(build("achterberg", ["Hans Vogel <h.vogel@uni-bonn.example.de>"],
        "Besuch im Juli / visit in July",
        """Lieber Hans,

vielen Dank für die Einladung nach Bonn. Ich könnte im Juli zwei Wochen kommen
und über die Präriebienen sprechen. Für die Wildbienen-Bestimmung würde ich
gerne Eure Sammlung der Andrena-Arten ansehen.

Herzliche Grüße, Miriam""", d(2009, 3, 11, 20, 0, CST), charset="iso-8859-1"),
        "moderate", "Correspondence with collaborators; early career (pre-survey) international work",
        "German-language letter planning a 2009 research visit to Bonn",
        "Achterberg writes in German (ISO-8859-1 encoded) accepting an invitation to visit Bonn for two weeks, to speak about prairie bees and examine a collection of Andrena species.",
        ["international collaboration", "German", "Andrena", "research visit"],
        diff="subtle", tags=["non_utf8_encoding", "non_english"])

    return M


def run():
    msgs = messages()
    # Loose .eml files, foldered like a mail client export
    loose_folders = {
        "high": "Email/Saved_Messages/Prairie_Bee_Survey",
        "moderate": "Email/Saved_Messages/Professional",
        "low": "Email/Saved_Messages/Misc",
        "none": "Email/Saved_Messages/Misc",
    }
    for i, m in enumerate(msgs):
        subj = m["msg"]["Subject"]
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in subj)[:60].strip()
        rel = f"{loose_folders[m['rel']]}/{i:02d}_{safe}.eml"
        reg.p(rel).write_bytes(bytes(m["msg"]))
        date = m["msg"]["Date"]
        reg.add(rel, m["rel"], m["why"], lane="email", title=m["title"], summary=m["summary"],
                keywords=m["kw"], sens=m["sens"], difficulty=m["diff"], tags=m["tags"],
                fmt="message/rfc822", date=date)

    # mbox export containing a subset plus mail that exists only here
    mb_rel = "Email/Thunderbird_Export/Inbox_2019-2021.mbox"
    path = reg.p(mb_rel)
    if path.exists():
        path.unlink()
    box = mailbox.mbox(str(path))
    member_ids = []
    for m in msgs[:12]:
        box.add(m["msg"])
        member_ids.append(m["msg"]["Message-ID"])
    box.flush()
    box.close()
    reg.add(mb_rel, "high", "Mailbox containing correspondence with collaborators, students, DNR and landowners about the survey",
            lane="email", title="Inbox export 2019-2021 (mbox)",
            summary="Thunderbird mbox export of 12 messages from 2019-2021, mostly Prairie Bee Survey correspondence (methods, reviews, DNR location guidance, landowner history) mixed with a few routine messages. Several messages also exist as loose .eml files.",
            keywords=["mbox", "mailbox", "correspondence"], sens=("sensitive_location", "pii_contact"),
            action="expand_container", fmt="application/mbox", tags=["container", "contains_duplicates"],
            difficulty="subtle")
    for m in msgs[:12]:
        reg.add(m["msg"]["Message-ID"], m["rel"], m["why"], lane="email", title=m["title"],
                summary=m["summary"], keywords=m["kw"], sens=m["sens"], difficulty=m["diff"],
                tags=m["tags"] + ["mbox_member", "duplicate_of_loose_eml"], fmt="message/rfc822",
                container=f"{ROOT_NAME}/{mb_rel}")

    reg.folder("Email", "high", "Exported email: saved .eml messages sorted by the donor into research, professional and miscellaneous folders, plus a Thunderbird mbox export.")
    reg.folder("Email/Saved_Messages/Prairie_Bee_Survey", "high", "Research correspondence about the Prairie Bee Survey: methods, statistical results, peer review, DNR location policy, landowner history.")
    reg.folder("Email/Saved_Messages/Professional", "moderate", "Career and outreach correspondence: media request, seminar logistics, dissertation advising, international visit.")
    reg.folder("Email/Saved_Messages/Misc", "low", "Mixed miscellany: building/IT notices, vendor spam, phishing, newsletters, plus restricted personnel, family and student messages.")
    return msgs
