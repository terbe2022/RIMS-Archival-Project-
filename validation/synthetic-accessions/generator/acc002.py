"""ACC-SYN-2026-002: administrative office shared drive (Office of the Associate Dean for
Academic Programs, CAES). Exercises the administrative ruleset: final vs superseded drafts,
committee minutes, retention-eligible transactional records, heavy duplication and sync
conflict copies, personnel and student-record restrictions. All content is invented."""
from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import docx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from pptx import Presentation
from pptx.util import Inches as PInches
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle

from common import Registry, rng
from gen_emails import build, d, CDT, CST
from gen_media import tts, ff, exif_bytes


def save_jpg(im, rel, dt, gps=None, make="Canon", model="EOS 80D"):
    ex = exif_bytes(dt, make, model, *(gps or (None, None)))
    im.save(reg.p(rel), "JPEG", quality=88, exif=ex.tobytes())

reg = Registry("ADAP_Office_Share")
SS = getSampleStyleSheet()
ROOTN = "ADAP_Office_Share"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

DOM = "caes.illinois.example.edu"
P = {
    "whitcomb": f"Leonard Whitcomb <lwhitcomb@{DOM}>", "rao": f"Sunita Rao <srao@{DOM}>",
    "kowal": f"Brenda Kowal <bkowal@{DOM}>", "hale": f"Marcus Hale <mhale@{DOM}>",
    "dean": f"Patricia Okafor-Grant <dean@{DOM}>", "provost": "Office of the Provost <provost@illinois.example.edu>",
    "chairs": f"CAES Department Heads <caes-heads@{DOM}>", "faculty": f"CAES Faculty <caes-faculty@{DOM}>",
}


# ------------------------------------------------------------------ helpers
def A(rel, relevance, why, **kw):
    reg.add(rel, relevance, why, **kw)


def png_chart(kind, title, xs, series, ylabel=""):
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    if kind == "line":
        for name, ys in series.items():
            ax.plot(xs, ys, marker="o", label=name)
    elif kind == "bar":
        w = 0.8 / len(series)
        for i, (name, ys) in enumerate(series.items()):
            ax.bar([j + i * w for j in range(len(xs))], ys, w, label=name)
        ax.set_xticks([j + 0.4 - w / 2 for j in range(len(xs))]); ax.set_xticklabels(xs, rotation=30, ha="right", fontsize=7)
    ax.set_title(title); ax.set_ylabel(ylabel)
    if len(series) > 1:
        ax.legend(fontsize=7, frameon=False)
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=150, bbox_inches="tight"); plt.close(fig)
    return b.getvalue()


def write_docx(rel, title, paras, comments=None, author="ADAP"):
    dd = docx.Document()
    dd.core_properties.author = author; dd.core_properties.title = title
    dd.add_heading(title, 1)
    for p in paras:
        if p.startswith("## "):
            dd.add_heading(p[3:], 2)
        else:
            dd.add_paragraph(p)
    if comments:
        dd.add_heading("Reviewer comments", 2)
        for c in comments:
            dd.add_paragraph(c, style="List Bullet")
    dd.save(reg.p(rel))


def write_pdf(rel, title, paras, images=(), table=None, small=None):
    story = [Paragraph(title, SS["Title"])]
    for p in paras:
        story.append(Paragraph(p[3:], SS["Heading2"]) if p.startswith("## ") else Paragraph(p, SS["BodyText"]))
    for png in images:
        story += [Spacer(1, 6), RLImage(io.BytesIO(png), width=5 * inch, height=3.1 * inch)]
    if table:
        t = Table(table); t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .3, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("FONTSIZE", (0, 0), (-1, -1), 8)]))
        story += [Spacer(1, 6), t]
    if small:
        story.append(Paragraph(small, SS["Italic"]))
    SimpleDocTemplate(str(reg.p(rel)), pagesize=letter, title=title).build(story)


def write_xlsx(rel, sheets, chart=None):
    wb = Workbook(); first = True
    for name, rows in sheets.items():
        ws = wb.active if first else wb.create_sheet(name)
        ws.title = name; first = False
        for r in rows:
            ws.append(list(r))
    if chart:
        wb.create_sheet("Chart").add_image(XLImage(io.BytesIO(chart)), "A1")
    wb.save(reg.p(rel))


def scan(rel, lines, title_line, signature=None, size=(1275, 1650), fmt="PDF"):
    im = Image.new("L", size, 246); dr = ImageDraw.Draw(im)
    fb = ImageFont.truetype(FONT.replace("Sans.ttf", "Sans-Bold.ttf"), 30); f = ImageFont.truetype(FONT, 24)
    dr.text((90, 80), title_line, font=fb, fill=20)
    y = 160
    for ln in lines:
        dr.text((90, y), ln, font=f, fill=35); y += 38
    if signature:
        dr.line([(90, y + 80), (520, y + 70)], fill=30, width=3)
        dr.text((90, y + 95), signature, font=f, fill=35)
    im = im.rotate(-0.8, fillcolor=230)
    im = Image.blend(im, Image.effect_noise(size, 30).convert("L"), 0.07).filter(ImageFilter.GaussianBlur(0.7))
    if fmt == "PDF":
        im.convert("RGB").save(reg.p(rel), "PDF", resolution=150)
    else:
        im.save(reg.p(rel), "TIFF", compression="group4" if False else "tiff_lzw")


def soffice(src: Path, fmt: str, outdir: Path) -> Path:
    subprocess.run(["soffice", "--headless", "--convert-to", fmt, "--outdir", str(outdir), str(src)], check=True, capture_output=True, timeout=180)
    return outdir / (src.stem + "." + fmt)


def dup(src_rel, dst_rel, why="Exact duplicate of a file kept elsewhere in the transfer", action="exclude_duplicate", tags=("duplicate_exact",)):
    shutil.copy(reg.root / src_rel, reg.p(dst_rel))
    o = reg.labels[f"{ROOTN}/{src_rel}"]
    A(dst_rel, o.relevance, why, lane=o.lane, fmt=o.true_format, title=o.gt_title + " (copy)",
      summary=f"Copy of {src_rel}.", keywords=o.gt_keywords, sens=o.sensitivity, action=action,
      duplicate_of=f"{ROOTN}/{src_rel}", tags=list(tags), date=o.nominal_date, difficulty="subtle")


# ------------------------------------------------------------------ policies
AIP_V1 = ["## Purpose", "This policy describes how the College handles suspected academic integrity violations in undergraduate courses.",
          "## Procedure", "An instructor who suspects a violation meets with the student, documents the evidence, and may assign a sanction up to failure of the course.",
          "## Appeals", "Students may appeal to the Associate Dean within 10 business days."]
AIP_V2 = AIP_V1[:4] + ["A second documented violation in any CAES course is referred automatically to the College Academic Integrity Board, which may recommend suspension (the 'two-strike' rule).",
                       "Instructors must report every finding to the Associate Dean's office within 5 business days so that repeat violations can be identified."] + AIP_V1[4:]
AIP_V3 = [p.replace("business days", "working days") for p in AIP_V2]
AIP_2021 = AIP_V2[:4] + ["Revised 2021: the two-strike referral no longer applies to violations committed during a student's first semester. First-semester findings trigger a required educational module instead.",
                         "During remote instruction, unauthorized use of online solution sites is treated as unauthorized collaboration."] + AIP_V2[6:]


def build_policies():
    PL = "Policies/Academic_Integrity"
    write_docx(f"{PL}/drafts/AI_Policy_draft_v1_2015-09.docx", "CAES Academic Integrity Policy - DRAFT v1", AIP_V1, author="L. Whitcomb")
    A(f"{PL}/drafts/AI_Policy_draft_v1_2015-09.docx", "moderate", "Draft policy; superseded but first version of the policy", lane="document", fmt="docx", date="2015-09-14",
      title="Academic integrity policy, first draft (2015)", summary="First draft of the college academic integrity procedure: instructor meeting, documentation, sanctions up to course failure, appeal to the associate dean.",
      keywords=["academic integrity", "policy draft"], difficulty="subtle", tags=["version_series"])
    write_docx(f"{PL}/drafts/AI_Policy_draft_v2_2015-11.docx", "CAES Academic Integrity Policy - DRAFT v2", AIP_V2,
               comments=["MH: two-strike rule is the big change - check with Legal", "LW: reporting deadline 5 days OK?"], author="L. Whitcomb")
    A(f"{PL}/drafts/AI_Policy_draft_v2_2015-11.docx", "high", "Draft that shows a significant change in policy (introduces two-strike referral)", lane="document", fmt="docx (with comments section)",
      date="2015-11-02", title="Academic integrity policy draft v2 introducing two-strike rule",
      summary="Second draft adding the two-strike referral to an Academic Integrity Board and mandatory reporting to the dean's office, with staff comments flagging the change for legal review.",
      keywords=["academic integrity", "two-strike rule", "policy change"], difficulty="subtle", tags=["version_series"])
    write_docx(f"{PL}/drafts/AI_Policy_draft_v3_2015-12.docx", "CAES Academic Integrity Policy - DRAFT v3", AIP_V3, author="M. Hale")
    A(f"{PL}/drafts/AI_Policy_draft_v3_2015-12.docx", "low", "Superseded draft with no significant change (wording only)", lane="document", fmt="docx", date="2015-12-01",
      title="Academic integrity policy draft v3 (wording edits)", summary="Third draft identical to v2 except 'business days' changed to 'working days'.",
      keywords=["policy draft", "superseded"], difficulty="subtle", tags=["version_series", "near_duplicate_text"])
    write_pdf(f"{PL}/AI_Policy_FINAL_approved_2016-02.pdf", "CAES Academic Integrity Policy (Approved February 2016)", AIP_V3,
              small="Approved by the CAES Executive Committee, 9 February 2016. Effective Fall 2016.")
    A(f"{PL}/AI_Policy_FINAL_approved_2016-02.pdf", "high", "Final, approved version of a college academic policy", lane="document", fmt="pdf", date="2016-02-09",
      title="CAES Academic Integrity Policy, approved 2016", summary="Approved college academic integrity policy with instructor procedure, two-strike referral to the Academic Integrity Board, mandatory reporting and appeals.",
      keywords=["academic integrity", "approved policy", "two-strike rule"])
    write_docx(f"{PL}/AI_Policy_REVISED_2021_FINAL.docx", "CAES Academic Integrity Policy (Revised 2021) - FINAL", AIP_2021, author="S. Rao")
    A(f"{PL}/AI_Policy_REVISED_2021_FINAL.docx", "high", "Final, approved version of a revised policy (significant change)", lane="document", fmt="docx", date="2021-04-20",
      title="Academic integrity policy revised 2021", summary="2021 revision exempting first-semester students from the two-strike referral in favour of an educational module, and treating online solution sites as unauthorized collaboration during remote instruction.",
      keywords=["academic integrity", "policy revision", "remote instruction", "first-year students"])
    GA = ["## Scope", "Applies to final course grades in CAES undergraduate courses.", "## Steps",
          "1. Student contacts instructor within 30 days of grade posting. 2. If unresolved, written appeal to the department head. 3. Final appeal to the Associate Dean, whose decision is final.",
          "## Grounds", "Arithmetic error, application of standards different from those applied to other students, or departure from the syllabus."]
    write_docx("Policies/Grade_Appeals/Grade_Appeal_Procedure_2018_FINAL.docx", "CAES Grade Appeal Procedure (2018) - FINAL", GA, author="S. Rao")
    A("Policies/Grade_Appeals/Grade_Appeal_Procedure_2018_FINAL.docx", "high", "Final, approved college academic procedure", lane="document", fmt="docx", date="2018-08-20",
      title="CAES grade appeal procedure 2018", summary="Three-step grade appeal procedure (instructor, department head, associate dean) with permitted grounds for appeal.",
      keywords=["grade appeal", "procedure", "policy"])
    # OneDrive conflict copy: near-identical
    write_docx("Policies/Grade_Appeals/Grade_Appeal_Procedure_2018_FINAL-BKOWAL-LT.docx", "CAES Grade Appeal Procedure (2018) - FINAL", GA[:4] + [GA[4].replace("30 days", "30 calendar days")] + GA[5:], author="B. Kowal")
    A("Policies/Grade_Appeals/Grade_Appeal_Procedure_2018_FINAL-BKOWAL-LT.docx", "high", "OneDrive sync conflict copy with a one-word difference",
      lane="document", fmt="docx", date="2018-09-04", title="Grade appeal procedure (sync conflict copy)",
      summary="OneDrive conflict copy of the 2018 grade appeal procedure, created on a staff laptop; differs only by 'calendar' in one sentence. Needs a human to confirm which is authoritative.",
      keywords=["sync conflict", "near duplicate"], action="review_near_duplicate", tags=["sync_conflict", "near_duplicate_text"], difficulty="ambiguous")
    # Legacy 2012 policy (.doc) and its website copy
    with tempfile.TemporaryDirectory() as td:
        write_docx("_tmp.docx", "CAES Course Repeat Policy (2012)", ["Students may repeat a CAES course once for grade replacement. Both attempts remain on the transcript.",
                                                                 "Approved by the CAES Executive Committee, May 2012."])
        src = reg.root / "_tmp.docx"; tmp = Path(td) / "Course_Repeat_Policy_2012.docx"; shutil.move(src, tmp)
        out = soffice(tmp, "doc", Path(td)); shutil.copy(out, reg.p("Policies/Course_Repeat/Course_Repeat_Policy_2012.doc"))
    A("Policies/Course_Repeat/Course_Repeat_Policy_2012.doc", "high", "Final approved college academic policy (legacy format)", lane="document", fmt="doc (legacy OLE2)", date="2012-05-15",
      title="CAES course repeat policy 2012", summary="Legacy Word document of the 2012 policy allowing one grade-replacement repeat per course.",
      keywords=["course repeat", "policy", "legacy format"], tags=["legacy_format"])
    html = "<html><head><title>CAES Academic Policies</title></head><body><nav>Home | Students | Faculty</nav><h1>Academic Integrity</h1>" + "".join(
        f"<p>{p}</p>" for p in AIP_V3 if not p.startswith("##")) + "<footer>Last updated 2016</footer></body></html>"
    reg.p("Website_Content/policies_academic_integrity.html").write_text(html)
    A("Website_Content/policies_academic_integrity.html", "low", "Web copy of a policy whose approved final is kept elsewhere", lane="document", fmt="text/html", date="2016-03-01",
      title="College website page: academic integrity policy", summary="Saved web page reproducing the 2016 academic integrity policy text with site navigation.",
      keywords=["website", "policy", "copy"], tags=["same_content_different_format"], difficulty="ambiguous")
    reg.folder("Policies", "high", "College academic policies: final approved versions, drafts showing major changes, superseded drafts, sync conflicts, legacy format.")


# ------------------------------------------------------------------ curriculum committee
ACTIONS = {
    2014: [("AGRON 101", "new course", "approved"), ("FSHN 220", "revision", "approved")],
    2015: [("NRES 310", "new course", "approved"), ("AGRON 340", "prerequisite change", "approved")],
    2016: [("ACES 101", "new first-year seminar", "approved"), ("ANSC 199", "special topics", "tabled")],
    2017: [("HORT 199 Cannabis Cultivation", "new course", "rejected - legal concerns"), ("NRES 420", "revision", "approved")],
    2018: [("Sustainable Food Systems BS", "new major", "approved for campus review"), ("FSHN 101", "online section", "approved")],
    2019: [("ACES 199 Data Literacy", "new course", "approved"), ("AGRON 101", "credit hours 3->4", "approved")],
    2020: [("All courses", "emergency remote delivery", "approved by chair under emergency authority"), ("Pass/No Pass", "temporary grading option", "endorsed")],
    2021: [("NRES 310", "permanent online version", "approved"), ("ACES 101", "retire", "deferred")],
    2022: [("Sustainable Food Systems BS", "first-year review", "accepted"), ("Agricultural Communications minor", "new minor", "approved")],
}


def build_curriculum():
    for year, actions in ACTIONS.items():
        for mi, (mon, day) in enumerate([(10, 8), (3, 4)]):
            y = year if mon > 6 else year + 1
            date = f"{y}-{mon:02d}-{day:02d}"
            act = actions[mi]
            base = f"Curriculum_Committee/{year}-{year + 1}"
            agenda = [f"CAES Curriculum Committee - {date}", "1. Approval of previous minutes", f"2. {act[0]}: {act[1]}", "3. Announcements", "4. Adjourn"]
            write_docx(f"{base}/Agenda_{date}.docx", f"Curriculum Committee Agenda {date}", agenda[1:])
            A(f"{base}/Agenda_{date}.docx", "high", "Agendas of the college Curriculum Committee", lane="document", fmt="docx", date=date,
              title=f"Curriculum Committee agenda, {date}", summary=f"Agenda for the {date} Curriculum Committee meeting; main item {act[0]} ({act[1]}).",
              keywords=["curriculum committee", "agenda", act[0]], tags=["series"])
            minutes = [f"Present: Whitcomb (chair) and 7 members" if y < 2018 else "Present: Rao (chair) and 8 members",
                       f"Item: {act[0]} - {act[1]}.",
                       f"Discussion: members discussed enrollment demand, staffing and overlap with existing courses. "
                       + ("Concerns were raised about federal law and the university's drug-free campus policy. " if "Cannabis" in act[0] else "")
                       + ("The chair invoked emergency authority given the campus closure. " if year == 2020 else ""),
                       f"Outcome: {act[2]}.", "Meeting adjourned 4:52 pm. Minutes: M. Hale."]
            rel = f"{base}/Minutes_{date}.docx"
            if year in (2014, 2017) and mi == 1:     # some minutes only as signed scans
                rel = f"{base}/Minutes_{date}_signed.pdf"
                scan(rel, [f"Date: {date}"] + minutes, "CAES CURRICULUM COMMITTEE - MINUTES", signature="Approved: L. Whitcomb, Chair")
                fmt, tags = "pdf (image-only signed scan)", ["series", "scanned_image_pdf", "needs_ocr"]
            else:
                write_docx(rel, f"Curriculum Committee Minutes {date}", minutes)
                fmt, tags = "docx", ["series"]
            A(rel, "high", "Minutes of the college Curriculum Committee", lane="document", fmt=fmt, date=date,
              title=f"Curriculum Committee minutes, {date}: {act[0]} {act[2].split(' -')[0]}",
              summary=f"Minutes recording the committee's action on {act[0]} ({act[1]}): {act[2]}.", keywords=["curriculum committee", "minutes", act[0]], tags=tags,
              difficulty="obvious" if fmt == "docx" else "subtle")
    # proposals
    PR = "Curriculum_Committee/Proposals"
    write_docx(f"{PR}/HORT199_Cannabis_Cultivation_proposal.docx", "New Course Proposal: HORT 199 Cannabis Cultivation",
               ["Rationale: student demand and industry growth in states with legal markets.", "Learning outcomes: plant physiology, regulation, greenhouse management.",
                "Committee decision (2018-03-04): REJECTED. Legal counsel advised the course could conflict with federal funding requirements."])
    A(f"{PR}/HORT199_Cannabis_Cultivation_proposal.docx", "high", "Rejected course proposals are kept", lane="document", fmt="docx", date="2018-03-04",
      title="Rejected course proposal: HORT 199 Cannabis Cultivation", summary="New course proposal for cannabis cultivation with rationale and outcomes, annotated as rejected on legal counsel's advice.",
      keywords=["course proposal", "rejected", "cannabis"], difficulty="subtle")
    proj = png_chart("line", "Projected enrollment, Sustainable Food Systems BS", [2019, 2020, 2021, 2022, 2023],
                     {"Projected": [25, 60, 95, 130, 150], "Break-even": [80] * 5}, "students")
    write_pdf(f"{PR}/Sustainable_Food_Systems_BS_proposal_2018.pdf", "Proposal: B.S. in Sustainable Food Systems",
              ["## Rationale", "A cross-departmental major combining agronomy, food science, economics and policy, responding to employer demand.",
               "## Curriculum", "120 credit hours; 5 core courses; 3 concentrations: production, processing, policy.",
               "## Resources", "Two new faculty lines requested; existing courses absorb first two cohorts."], images=[proj],
              table=[["Year", "New students", "Total"], ["2019", "25", "25"], ["2020", "40", "60"], ["2021", "45", "95"]])
    A(f"{PR}/Sustainable_Food_Systems_BS_proposal_2018.pdf", "high", "Approved program proposals", lane="document", fmt="pdf (text + chart + table)", date="2018-10-08",
      title="Proposal for a B.S. in Sustainable Food Systems", summary="New-major proposal with rationale, curriculum structure, resource requests, a projected-enrollment chart and enrollment table.",
      keywords=["new major", "program proposal", "Sustainable Food Systems"], tags=["mixed_media_pdf", "charts_in_pdf"])
    write_docx(f"{PR}/ACES199_Data_Literacy_proposal.docx", "New Course Proposal: ACES 199 Data Literacy for Agriculture",
               ["Introduces spreadsheets, basic statistics and visualization with agricultural datasets.", "Committee decision (2019-10-08): APPROVED."])
    A(f"{PR}/ACES199_Data_Literacy_proposal.docx", "high", "Approved course proposals", lane="document", fmt="docx", date="2019-10-08",
      title="Approved course proposal: ACES 199 Data Literacy", summary="Course proposal for an introductory agricultural data literacy course, approved October 2019.",
      keywords=["course proposal", "approved", "data literacy"])
    # zip of 2014-2016 minutes (duplicates)
    import zipfile
    zrel = "Curriculum_Committee/Curriculum_Committee_2014-2016_ARCHIVE.zip"
    with zipfile.ZipFile(reg.p(zrel), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted((reg.root / "Curriculum_Committee").glob("201[456]-*/*")):
            z.write(f, f.relative_to(reg.root / "Curriculum_Committee"))
            o = reg.labels[f"{ROOTN}/{f.relative_to(reg.root)}"]
            reg.add(str(f.relative_to(reg.root / "Curriculum_Committee")), o.relevance, o.relevance_rationale, lane=o.lane, fmt=o.true_format,
                    title=o.gt_title, summary=o.gt_summary, keywords=o.gt_keywords, container=f"{ROOTN}/{zrel}",
                    action="exclude_duplicate", duplicate_of=o.path, tags=["archive_member", "duplicate_exact"])
    A(zrel, "high", "Committee minutes (zipped duplicate set)", lane="archive", fmt="zip", date="2017-07-01",
      title="ZIP of Curriculum Committee records 2014-2016", summary="ZIP archive duplicating the 2014-2016 Curriculum Committee agendas and minutes kept in their year folders.",
      keywords=["zip", "duplicates", "curriculum committee"], action="expand_container", tags=["container", "contains_duplicates"], difficulty="subtle")
    reg.folder("Curriculum_Committee", "high", "Curriculum Committee agendas and minutes 2014-2023 (some as signed scans), course and program proposals, a duplicate ZIP.")


# ------------------------------------------------------------------ program review, accreditation, strategic plan, annual reports
def build_reviews_plans():
    PRV = "Program_Review/Agronomy_BS_2017"
    enr = png_chart("line", "Agronomy BS enrollment", list(range(2010, 2017)), {"Majors": [212, 225, 241, 238, 256, 270, 281]}, "students")
    out = png_chart("bar", "Graduate outcomes (6 months)", ["Employed", "Grad school", "Seeking", "Unknown"], {"2015": [71, 14, 6, 9], "2016": [74, 12, 5, 9]}, "%")
    write_pdf(f"{PRV}/Agronomy_BS_Self-Study_2017.pdf", "Agronomy B.S. Program Review: Self-Study (2017)",
              ["## Program overview", "The Agronomy B.S. enrolls about 280 majors in three concentrations.",
               "## Strengths", "Strong placement; growing enrollment; hands-on research farm courses.",
               "## Challenges", "Faculty retirements; capstone course capacity; limited diversity of majors (12% underrepresented)."],
              images=[enr, out], table=[["Year", "Majors", "Degrees"], ["2014", "256", "61"], ["2015", "270", "66"], ["2016", "281", "70"]])
    A(f"{PRV}/Agronomy_BS_Self-Study_2017.pdf", "high", "Program review self-studies", lane="document", fmt="pdf (text + 2 charts + table)", date="2017-02-15",
      title="Agronomy B.S. program review self-study 2017", summary="Self-study with program overview, strengths, challenges, an enrollment trend chart, graduate outcome chart and degree table.",
      keywords=["program review", "self-study", "Agronomy", "enrollment"], tags=["mixed_media_pdf", "charts_in_pdf"])
    write_pdf(f"{PRV}/External_Reviewers_Report_2017.pdf", "External Review Team Report: Agronomy B.S.",
              ["The team commends the program's experiential learning.", "Recommendations: (1) add a second capstone section; (2) recruit transfer students from community colleges; (3) hire in soil science."])
    A(f"{PRV}/External_Reviewers_Report_2017.pdf", "high", "External reviewer reports", lane="document", fmt="pdf", date="2017-04-20",
      title="External reviewers' report on Agronomy B.S.", summary="External review report praising experiential learning and recommending a second capstone, transfer recruitment and a soil science hire.",
      keywords=["external review", "recommendations"])
    write_docx(f"{PRV}/Department_Response_2017.docx", "Department Response to External Review",
               ["Capstone: second section added Fall 2018.", "Transfer recruitment: articulation agreements with 3 community colleges.", "Soil science hire: requested in FY19 budget."])
    A(f"{PRV}/Department_Response_2017.docx", "high", "Responses to program reviews", lane="document", fmt="docx", date="2017-06-01",
      title="Department response to Agronomy program review", summary="Department's response committing to a second capstone section, community college articulation, and a soil science hire request.",
      keywords=["program review", "response"])
    write_docx(f"{PRV}/site_visit_schedule.docx", "Site Visit Schedule - April 18-19, 2017",
               ["8:00 breakfast with Dean (Room 112)", "9:00 tour of research farm", "12:00 lunch with students", "3:00 exit interview"])
    A(f"{PRV}/site_visit_schedule.docx", "low", "Logistics of the review (routine)", lane="document", fmt="docx", date="2017-04-10",
      title="Program review site-visit schedule", summary="Two-day itinerary for external reviewers' site visit.", keywords=["schedule", "logistics"], difficulty="subtle")
    write_pdf(f"{PRV}/catering_invoice_0418.pdf", "INVOICE #4471 - Campus Catering", ["Breakfast for 12: $186.00", "Lunch for 20: $340.00", "Total due: $526.00"])
    A(f"{PRV}/catering_invoice_0418.pdf", "none", "Routine transactional records past retention (catering)", lane="document", fmt="pdf", date="2017-04-25",
      title="Catering invoice for site visit", summary="Catering invoice for the program review site visit.", keywords=["invoice", "catering"], tags=["retention_eligible"])

    AC = "Accreditation/HLC_2017"
    write_docx(f"{AC}/Criterion3_CAES_contribution.docx", "HLC Criterion 3 (Teaching and Learning) - CAES contribution",
               ["3.A Degree programs are appropriate to higher education: CAES learning outcomes mapped for all 11 majors.",
                "3.B General education: CAES courses contributing to campus gen-ed listed in evidence file E-3B-07.",
                "3.C Faculty: 94% of CAES undergraduate credit hours taught by faculty with terminal degrees."])
    A(f"{AC}/Criterion3_CAES_contribution.docx", "high", "Accreditation reports", lane="document", fmt="docx", date="2017-01-30",
      title="College contribution to accreditation Criterion 3", summary="College narrative for institutional accreditation on degree program outcomes, general education and faculty qualifications.",
      keywords=["accreditation", "HLC", "Criterion 3"])
    write_xlsx(f"{AC}/Evidence_Index_CAES.xlsx", {"Evidence": [("ID", "Description", "File"), ("E-3A-01", "Learning outcomes, all majors", "outcomes_map.pdf"),
                                                                ("E-3B-07", "Gen-ed course list", "gened_list.xlsx"), ("E-3C-02", "Faculty credentials summary", "credentials.xlsx")]})
    A(f"{AC}/Evidence_Index_CAES.xlsx", "high", "Accreditation evidence", lane="tabular", fmt="xlsx", date="2017-01-30",
      title="Accreditation evidence index", summary="Index of accreditation evidence items with IDs, descriptions and file names.", keywords=["accreditation", "evidence index"], difficulty="subtle")
    scan(f"{AC}/HLC_action_letter_2017.tif", ["Dear President:", "The Higher Learning Commission (synthetic) has continued the", "University's accreditation with the next comprehensive",
                                             "evaluation in 2026-27. No interim monitoring is required.", "", "Sincerely, Commission Staff"], "ACTION LETTER", fmt="TIFF")
    A(f"{AC}/HLC_action_letter_2017.tif", "high", "Accreditation reports and outcomes", lane="image", fmt="tiff (scanned letter)", date="2017-08-01",
      title="Accreditation action letter 2017 (scan)", summary="Scanned accreditor letter continuing accreditation with next comprehensive evaluation in 2026-27 and no interim monitoring.",
      keywords=["accreditation", "action letter", "OCR"], tags=["needs_ocr", "text_in_image"], difficulty="subtle")

    SP = "Strategic_Plan_2019-2024"
    base = ["## Vision", "CAES will be the leading public college for food, agriculture and the environment.", "## Goals"]
    goals = ["1. Expand experiential learning to every student.", "2. Grow enrollment of underrepresented students.", "3. Modernize facilities."]
    versions = {1: (base + goals, "high", "Draft showing a significant change (first draft establishing goals)", "First draft setting out the vision and three goals."),
                2: (base + goals + ["(formatting fixes)"], "low", "Superseded draft with no significant change", "Second draft identical in substance to v1 with formatting fixes."),
                3: (base + goals[:2] + ["3. Become carbon neutral in college operations by 2035."], "high", "Draft showing a significant change (facilities goal replaced by carbon neutrality)",
                    "Third draft replacing the facilities goal with a 2035 carbon-neutrality goal after town hall feedback."),
                4: (base + goals[:2] + ["3. Become carbon neutral in college operations by 2035.", "(typo fixes)"], "low", "Superseded draft with no significant change", "Fourth draft with typo fixes only."),
                5: (base + goals[:2] + ["3. Become carbon neutral in college operations by 2035.", "4. Make data literacy a graduation competency."], "moderate",
                    "Late draft adding a fourth goal that appears in the final", "Fifth draft adding a data literacy competency goal, as adopted in the final.")}
    for v, (paras, rel_, why, summ) in versions.items():
        write_docx(f"{SP}/drafts/Strategic_Plan_DRAFT_v{v}.docx", f"CAES Strategic Plan 2019-2024 - DRAFT v{v}", paras, author="S. Rao")
        A(f"{SP}/drafts/Strategic_Plan_DRAFT_v{v}.docx", rel_, why, lane="document", fmt="docx", date=f"2019-0{v + 1}-15",
          title=f"Strategic plan draft v{v}", summary=summ, keywords=["strategic plan", "draft", f"v{v}"], tags=["version_series"], difficulty="subtle")
    write_pdf(f"{SP}/CAES_Strategic_Plan_2019-2024_FINAL.pdf", "CAES Strategic Plan 2019-2024", versions[5][0][:-0 or None] if False else [p for p in versions[5][0]])
    A(f"{SP}/CAES_Strategic_Plan_2019-2024_FINAL.pdf", "high", "The 2019-2024 strategic plan (final)", lane="document", fmt="pdf", date="2019-08-01",
      title="CAES strategic plan 2019-2024 (final)", summary="Final strategic plan with vision and four goals: experiential learning, underrepresented student enrollment, carbon neutrality by 2035, and data literacy.",
      keywords=["strategic plan", "final", "carbon neutrality", "data literacy"])
    agg = png_chart("bar", "Town hall survey: support for draft goals", ["Experiential", "Diversity", "Facilities", "Carbon neutral"],
                    {"Agree %": [88, 79, 41, 72]}, "%")
    write_xlsx(f"{SP}/survey/Strategic_Plan_Survey_RESULTS_aggregated.xlsx", {"Summary": [("Goal", "N", "Agree %"), ("Experiential learning", 412, 88), ("Diversity", 409, 79),
                                                                                        ("Facilities", 405, 41), ("Carbon neutral", 398, 72)]}, chart=agg)
    A(f"{SP}/survey/Strategic_Plan_Survey_RESULTS_aggregated.xlsx", "high", "Aggregated strategic-plan survey results", lane="tabular", fmt="xlsx (with chart image)", date="2019-04-01",
      title="Strategic plan survey: aggregated results", summary="Aggregated responses (about 400) showing low support for the facilities goal (41%) and 72% support for carbon neutrality, which explains the v3 change.",
      keywords=["survey", "aggregated results", "strategic plan"], tags=["embedded_image"])
    r = rng("spraw")
    rows = [("respondent", "role", "email", "q_facilities", "comment")]
    names = ["Ana Ruiz", "Ben Okoro", "Cara Lind", "Dev Patel", "Eli Shaw", "Fay Wu"]
    comments = ["Facilities are fine, focus on climate.", "Please fix Turner Hall roof first!", "Carbon neutral is unrealistic.", "More advising staff.", "", "Data skills matter for jobs."]
    for i in range(60):
        n = names[i % 6]
        rows.append((n + f" {i}", r.choice(["faculty", "staff", "student"]), f"{n.split()[0].lower()}{i}@illinois.example.edu", r.randint(1, 5), comments[i % 6]))
    with open(reg.p(f"{SP}/survey/raw_responses_WITH_NAMES.csv"), "w") as fh:
        import csv
        csv.writer(fh).writerows(rows)
    A(f"{SP}/survey/raw_responses_WITH_NAMES.csv", "moderate", "Raw survey responses (restricted: contain names); aggregated version is kept open", lane="tabular", fmt="text/csv", date="2019-04-01",
      title="Strategic plan survey raw responses with names", summary="Raw survey export of 60 responses with respondent names, emails, roles, ratings and comments.",
      keywords=["survey", "raw responses", "names"], sens=("pii_contact",), difficulty="ambiguous")
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[0]); s.shapes.title.text = "Strategic Planning Town Hall"; s.placeholders[1].text = "Sunita Rao - March 2019"
    sl = prs.slides.add_slide(prs.slide_layouts[5]); sl.shapes.title.text = "What you told us"
    sl.shapes.add_picture(io.BytesIO(agg), PInches(1.5), PInches(1.6), width=PInches(7))
    sl.notes_slide.notes_text_frame.text = "Facilities goal clearly unpopular - signal we will revisit."
    prs.save(reg.p(f"{SP}/Town_Hall_2019-03_slides.pptx"))
    A(f"{SP}/Town_Hall_2019-03_slides.pptx", "high", "Strategic plan town hall materials", lane="document", fmt="pptx (chart, notes)", date="2019-03-20",
      title="Strategic plan town hall slides", summary="Town hall deck with survey support chart and a speaker note signalling the facilities goal would be revisited.",
      keywords=["town hall", "strategic plan", "slides"], tags=["speaker_notes"])
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); w = td / "th.wav"
        tts("Good afternoon everyone. Thank you for coming to the strategic planning town hall. You told us clearly that facilities should not be a top goal. "
            "Many of you asked us to take climate seriously. So the next draft will propose that the college become carbon neutral by twenty thirty five.", w, voice="en-us+f4")
        im = Image.new("RGB", (1280, 720), (20, 50, 90)); ImageDraw.Draw(im).text((80, 320), "CAES Strategic Planning Town Hall - March 20, 2019", font=ImageFont.truetype(FONT, 40), fill=(255, 255, 255))
        im.save(td / "s.png")
        ff("-loop", "1", "-i", str(td / "s.png"), "-i", str(w), "-c:v", "libx264", "-tune", "stillimage", "-r", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(reg.p(f"{SP}/Town_Hall_2019-03_recording.mp4")))
    A(f"{SP}/Town_Hall_2019-03_recording.mp4", "high", "Recordings of town halls", lane="av", fmt="mp4 (static slide + speech)", date="2019-03-20",
      title="Recording of strategic plan town hall", summary="Recording in which the associate dean reports survey feedback against a facilities goal and announces a carbon-neutral-by-2035 goal for the next draft.",
      keywords=["town hall", "recording", "carbon neutral", "speech"], tags=["video", "audio_speech", "needs_transcription"])

    AR = "Annual_Reports"
    r = rng("ar")
    for y in range(2013, 2023):
        paras = [f"Academic year {y - 1}-{y}.", f"Curriculum actions: {r.randint(8, 30)} course changes, {r.randint(0, 3)} new programs.",
                 f"Academic integrity cases reported: {r.randint(20, 70)}.", f"Grade appeals reaching the dean: {r.randint(1, 9)}."]
        if y == 2020:
            paras.append("COVID-19: 1,140 course sections converted to remote delivery within 9 days; Pass/No Pass option used by 31% of students.")
        rel = f"{AR}/ADAP_Annual_Report_{y}." + ("pdf" if y >= 2018 else "docx")
        (write_pdf if y >= 2018 else write_docx)(rel, f"Office of the Associate Dean for Academic Programs - Annual Report {y}", paras)
        A(rel, "high", "Annual reports of the office", lane="document", fmt=rel.rsplit(".", 1)[1], date=f"{y}-07-15",
          title=f"ADAP annual report {y}", summary=f"Annual report for {y - 1}-{y} summarising curriculum actions, integrity cases and grade appeals" + (", including the COVID-19 remote conversion." if y == 2020 else "."),
          keywords=["annual report", str(y)], tags=["series"])
    reg.folder("Program_Review", "high", "Agronomy B.S. 2017 program review: self-study, external report, response, plus logistics and a catering invoice.")
    reg.folder("Accreditation", "high", "2017 institutional accreditation: college narrative, evidence index, scanned action letter.")
    reg.folder(SP, "high", "Strategic plan 2019-2024: five drafts (two with significant changes), final, town hall slides and recording, aggregated and raw survey data.")
    reg.folder(AR, "high", "Office annual reports 2013-2022.")


# ------------------------------------------------------------------ COVID, data, org charts
def build_covid_data():
    C = "COVID-19_Response"
    write_docx(f"{C}/Remote_Instruction_FAQ_v7.docx", "Remote Instruction FAQ for CAES Faculty (v7, April 2020)",
               ["Q: Must lectures be live? A: No. Recorded lectures are acceptable; hold at least one live office hour weekly.",
                "Q: Can I give a proctored exam? A: Use open-book alternatives where possible; remote proctoring requires the dean's approval.",
                "Q: What about lab courses? A: Departments may defer lab components to an incomplete (I) grade."])
    A(f"{C}/Remote_Instruction_FAQ_v7.docx", "high", "Guidance to faculty during COVID-19", lane="document", fmt="docx", date="2020-04-06",
      title="Remote instruction FAQ for faculty (COVID-19)", summary="Version 7 of the faculty FAQ for the remote shift: recorded lectures allowed, proctoring limited, lab components deferrable via incomplete grades.",
      keywords=["COVID-19", "remote instruction", "faculty guidance"])
    write_xlsx(f"{C}/Course_Modality_Tracker_Fall2020.xlsx", {"Fall2020": [("Course", "Section", "Modality", "Enrolled", "Instructor approved exemption")] +
                                                               [(f"{d_} {n}", s, m, e, x) for (d_, n, s, m, e, x) in [("AGRON", 101, "A", "Online", 240, "N"), ("AGRON", 340, "L1", "Hybrid", 24, "N"),
                                                                ("FSHN", 220, "A", "In person", 60, "Y"), ("NRES", 310, "A", "Online", 85, "N"), ("ANSC", 100, "AL", "Hybrid", 150, "N")]]})
    A(f"{C}/Course_Modality_Tracker_Fall2020.xlsx", "high", "Course modality tracking during COVID-19", lane="tabular", fmt="xlsx", date="2020-08-10",
      title="Fall 2020 course modality tracker", summary="Spreadsheet tracking delivery mode (online, hybrid, in person), enrolment and exemptions by course section for Fall 2020.",
      keywords=["COVID-19", "modality", "course sections"])
    rd = png_chart("bar", "Faculty readiness for remote teaching (n=212)", ["Video lectures", "LMS quizzes", "Online labs", "Proctoring"],
                   {"Comfortable %": [61, 74, 18, 22]}, "%")
    write_pdf(f"{C}/Faculty_Readiness_Survey_Results_2020-03.pdf", "Faculty Readiness Survey - March 2020", ["212 faculty responded within 48 hours.",
              "Most felt ready for video lectures and online quizzes; few for online labs or proctoring."], images=[rd])
    A(f"{C}/Faculty_Readiness_Survey_Results_2020-03.pdf", "high", "Faculty surveys during COVID-19", lane="document", fmt="pdf (text + chart)", date="2020-03-16",
      title="Faculty readiness survey results, March 2020", summary="Results of a 212-response faculty survey on readiness for remote teaching, with a bar chart: low readiness for online labs (18%) and proctoring (22%).",
      keywords=["COVID-19", "faculty survey", "remote teaching"], tags=["charts_in_pdf"])
    prs = Presentation(); s = prs.slides.add_slide(prs.slide_layouts[1]); s.shapes.title.text = "Zoom basics for teaching"
    s.placeholders[1].text = "Schedule meetings in the LMS\nUse waiting rooms\nRecord to cloud"; prs.save(reg.p(f"{C}/Zoom_training_slides.pptx"))
    A(f"{C}/Zoom_training_slides.pptx", "moderate", "COVID-19 response material, generic training content", lane="document", fmt="pptx", date="2020-03-14",
      title="Zoom training slides for faculty", summary="Single slide of generic Zoom teaching tips prepared during the remote shift.", keywords=["Zoom", "training"], difficulty="subtle")
    write_pdf(f"{C}/PO_2020-0412_hand_sanitizer.pdf", "PURCHASE ORDER 2020-0412", ["Vendor: Campus Stores", "48 x hand sanitizer 1L @ $9.10", "Total: $436.80"])
    A(f"{C}/PO_2020-0412_hand_sanitizer.pdf", "none", "Routine purchase orders past retention (even within the COVID folder)", lane="document", fmt="pdf", date="2020-04-12",
      title="Purchase order for hand sanitizer", summary="Purchase order for hand sanitizer during COVID-19.", keywords=["purchase order"], tags=["retention_eligible"], difficulty="subtle")
    im = Image.new("RGB", (1280, 800), (30, 30, 30)); dr = ImageDraw.Draw(im)
    for i in range(12):
        x, y = 20 + (i % 4) * 315, 20 + (i // 4) * 255
        dr.rectangle([x, y, x + 300, y + 240], fill=(60 + i * 8, 70, 90)); dr.ellipse([x + 110, y + 50, x + 190, y + 130], fill=(200, 170, 140))
        dr.text((x + 8, y + 215), f"Participant {i + 1}", fill=(255, 255, 255))
    im.save(reg.p(f"{C}/Screenshot_first_remote_dept_heads_meeting.png"))
    A(f"{C}/Screenshot_first_remote_dept_heads_meeting.png", "moderate", "Records documenting the COVID-19 response (visual record of first remote meeting)", lane="image",
      fmt="png (screenshot)", date="2020-03-17", title="Screenshot of first remote department heads meeting",
      summary="Screenshot of a video-call gallery of 12 participants from the first remote department heads meeting.", keywords=["screenshot", "Zoom", "COVID-19"], difficulty="ambiguous")

    D = "Data"
    yrs = list(range(2012, 2024))
    majors = {"Agronomy": [205, 212, 225, 241, 238, 256, 270, 281, 290, 284, 279, 286], "Food Science": [310, 305, 318, 322, 330, 341, 352, 349, 340, 333, 338, 344],
              "Sustainable Food Systems": [0] * 7 + [25, 58, 91, 127, 149]}
    ch = png_chart("line", "Undergraduate majors by program", yrs, majors, "students")
    write_xlsx(f"{D}/Enrollment_by_Major_2012-2023.xlsx", {"Enrollment": [("Year",) + tuple(majors)] + [(y,) + tuple(v[i] for v in majors.values()) for i, y in enumerate(yrs)]}, chart=ch)
    A(f"{D}/Enrollment_by_Major_2012-2023.xlsx", "high", "Aggregated enrollment data", lane="tabular", fmt="xlsx (with chart image)", date="2023-10-01",
      title="Enrollment by major 2012-2023", summary="Aggregated undergraduate headcount by major with a trend chart, showing the new Sustainable Food Systems major growing to 149 students.",
      keywords=["enrollment", "majors", "trend"], tags=["embedded_image"])
    with open(reg.p(f"{D}/DFW_rates_by_course_2016-2022.csv"), "w") as fh:
        fh.write("course,term,enrolled,dfw_rate\n" + "".join(f"{c},{t},{rng(c + t).randint(40, 300)},{rng(t + c).uniform(.03, .25):.3f}\n" for c in ["AGRON 101", "FSHN 220", "NRES 310", "ACES 101"] for t in ["FA16", "FA18", "FA20", "FA22"]))
    A(f"{D}/DFW_rates_by_course_2016-2022.csv", "high", "Aggregated course outcome data", lane="tabular", fmt="text/csv", date="2022-12-20",
      title="D/F/W rates by course 2016-2022", summary="Aggregated D, F and withdrawal rates by course and term for four gateway courses.", keywords=["DFW rates", "course outcomes"])
    r = rng("extract")
    with open(reg.p(f"{D}/extracts/student_enrollment_extract_FA2019.csv"), "w") as fh:
        fh.write("UIN,last,first,major,class,gpa,probation\n" + "".join(
            f"6{r.randint(10000000, 99999999)},{r.choice(['Kim', 'Diaz', 'Novak', 'Reyes', 'Shah'])},{r.choice(['Jo', 'Al', 'Mae', 'Raj', 'Lu'])},{r.choice(list(majors))},{r.choice(['FR', 'SO', 'JR', 'SR'])},{r.uniform(1.5, 4):.2f},{r.choice(['Y', 'N', 'N', 'N'])}\n" for _ in range(300)))
    A(f"{D}/extracts/student_enrollment_extract_FA2019.csv", "low", "Individual student records belong in the student records system (FERPA)", lane="tabular", fmt="text/csv", date="2019-09-15",
      title="Student-level enrollment extract Fall 2019", summary="Extract of 300 students with ID numbers, names, majors, GPA and probation status.", keywords=["student records", "extract"], sens=("ferpa_student",))
    reg.p(f"{D}/Enrollment_dashboard.twb").write_text(
        "<?xml version='1.0'?><workbook source-build='2020.1' xmlns:user='http://www.tableausoftware.com/xml/user'><datasources><datasource caption='Enrollment_by_Major_2012-2023' />"
        "</datasources><worksheets><worksheet name='Majors over time' /><worksheet name='SFS growth' /></worksheets></workbook>\n")
    A(f"{D}/Enrollment_dashboard.twb", "moderate", "Dashboard definition for aggregated data (no data embedded)", lane="code", fmt="Tableau workbook XML", date="2021-02-01",
      title="Tableau enrollment dashboard definition", summary="Tableau workbook XML defining two enrollment dashboards over the aggregated enrollment spreadsheet; holds no data itself.",
      keywords=["Tableau", "dashboard"], difficulty="ambiguous")
    with tempfile.TemporaryDirectory() as td:
        write_xlsx("_tmp.xlsx", {"Majors": [("Year", "Agronomy", "Food Science"), (2012, 205, 310), (2013, 212, 305)]})
        tmp = Path(td) / "enrollment_2013.xlsx"; shutil.move(reg.root / "_tmp.xlsx", tmp)
        out = soffice(tmp, "xls", Path(td)); shutil.copy(out, reg.p(f"{D}/old/enrollment_2013.xls"))
    A(f"{D}/old/enrollment_2013.xls", "moderate", "Aggregated enrollment data (early, superseded by the 2012-2023 workbook)", lane="tabular", fmt="xls (legacy BIFF8)", date="2013-10-01",
      title="Enrollment 2012-2013 (legacy Excel)", summary="Legacy Excel sheet of 2012-2013 headcounts for two majors, superseded by the full series.", keywords=["enrollment", "legacy format"], tags=["legacy_format"], difficulty="subtle")
    shutil.copy(reg.root / f"{D}/Enrollment_by_Major_2012-2023.xlsx", reg.p(f"{D}/Copy of Copy of Enrollment_by_Major_2012-2023.xlsx"))
    o = reg.labels[f"{ROOTN}/{D}/Enrollment_by_Major_2012-2023.xlsx"]
    A(f"{D}/Copy of Copy of Enrollment_by_Major_2012-2023.xlsx", o.relevance, "Exact duplicate", lane="tabular", fmt="xlsx", title=o.gt_title + " (copy of copy)",
      summary="Byte-identical copy of the enrollment workbook.", keywords=o.gt_keywords, action="exclude_duplicate", duplicate_of=o.path, tags=["duplicate_exact"], difficulty="subtle")

    OC = "Org_Charts"
    for y, people in [(2015, ["Associate Dean: L. Whitcomb", "Office Manager: B. Kowal", "Curriculum Coordinator: (vacant)"]),
                      (2019, ["Associate Dean: S. Rao", "Assistant Dean: J. Mbeki", "Office Manager: B. Kowal", "Curriculum Coordinator: M. Hale"])]:
        im = Image.new("RGB", (1200, 700), "white"); dr = ImageDraw.Draw(im); f = ImageFont.truetype(FONT, 26)
        dr.rectangle([450, 40, 750, 110], outline="black", width=3); dr.text((470, 60), "Dean P. Okafor-Grant", font=f, fill="black")
        for i, p in enumerate(people):
            x = 60 + i * 280; dr.line([(600, 110), (x + 120, 250)], fill="black", width=2)
            dr.rectangle([x, 250, x + 260, 330], outline="black", width=2); dr.text((x + 8, 275), p[:24], font=ImageFont.truetype(FONT, 18), fill="black")
        rel = f"{OC}/ADAP_org_chart_{y}." + ("png" if y == 2015 else "pdf")
        im.save(reg.p(rel), "PNG" if y == 2015 else "PDF")
        A(rel, "high", "Organizational charts", lane="image" if y == 2015 else "document", fmt="png (diagram)" if y == 2015 else "pdf (image-only diagram)",
          date=f"{y}-09-01", title=f"Office organizational chart {y}", summary=f"Organizational chart of the associate dean's office in {y}: " + "; ".join(people) + ".",
          keywords=["org chart", str(y)], tags=["text_in_image"], difficulty="subtle")
    reg.folder(C, "high", "COVID-19 response: faculty FAQ, modality tracker, readiness survey, training slides, screenshot, and a routine purchase order.")
    reg.folder(D, "high", "Institutional data: aggregated enrollment and outcomes (keep), a student-level extract (FERPA), a dashboard definition, legacy and duplicate copies.")
    reg.folder(OC, "high", "Organizational charts 2015 and 2019.")


# ------------------------------------------------------------------ correspondence
def build_mail():
    M = []
    def add(snd, to, subj, body, dt, rel, why, title, summ, kw, sens=("none",), diff="obvious", tags=()):
        M.append((build(P.get(snd, snd), [P.get(t, t) for t in to], subj, body, dt), rel, why, title, summ, kw, sens, diff, tags))
    add("rao", ["faculty"], "Moving to remote instruction effective March 23",
        "Colleagues,\n\nFollowing the Chancellor's announcement, all CAES courses will move to remote delivery effective Monday, March 23. Spring break is extended by one week to give you time to prepare. "
        "Please (1) post a revised syllabus by March 20, (2) complete the readiness survey today, and (3) contact your department's instructional designer.\n\nLab sections: departments may defer hands-on components using an Incomplete.\n\nSunita Rao\nAssociate Dean for Academic Programs",
        d(2020, 3, 12, 17, 4), "high", "Guidance to faculty during COVID-19 (associate dean correspondence setting policy)", "Associate dean's announcement of the move to remote instruction",
        "Associate dean instructs all faculty that courses move online on March 23 with an extended spring break, revised syllabi, a readiness survey and Incomplete grades for labs.", ["COVID-19", "remote instruction", "announcement"])
    add("rao", ["provost"], "CAES position on temporary Pass/No Pass grading",
        "The CAES Curriculum Committee endorses a temporary Pass/No Pass option for Spring 2020 with a late opt-in deadline (May 15). We ask that P grades satisfy prerequisite requirements for CAES majors. Data from our readiness survey attached in summary form.",
        d(2020, 3, 27, 11, 20), "high", "Correspondence of the associate dean that sets or explains policy", "College position on temporary Pass/No Pass grading",
        "Associate dean conveys the college's endorsement of a temporary Pass/No Pass option with a May 15 opt-in and requests that P grades satisfy prerequisites.", ["Pass/No Pass", "grading policy", "COVID-19"])
    add("whitcomb", ["Dr. Ian Forsythe <iforsythe@caes.illinois.example.edu>"], "Re: does the two-strike rule apply to my lab course?",
        "Ian, yes. The policy applies to all CAES undergraduate courses, including lab sections. A finding in your lab counts toward the two-strike total. If a student's first finding was in a non-CAES course, it does not count. Leonard",
        d(2016, 10, 3, 9, 30), "high", "Correspondence of the associate dean that explains/applies policy", "Interpretation of the two-strike rule for lab courses",
        "Associate dean explains to a faculty member that integrity findings in CAES lab sections count toward the two-strike rule while non-CAES findings do not.", ["academic integrity", "policy interpretation"], diff="subtle")
    add("rao", ["chairs"], "Grade distribution report and next steps",
        "Heads, attached is the five-year grade distribution report. Average GPA in 100-level CAES courses rose from 2.9 to 3.3. I am not proposing caps, but I ask each department to discuss grading norms and report back by May 1.",
        d(2022, 2, 14, 8, 45), "high", "Correspondence of the associate dean that sets direction on academic standards", "Memo to department heads on rising grades",
        "Associate dean shares a grade-distribution analysis showing 100-level GPA rising from 2.9 to 3.3 and asks departments to discuss grading norms.", ["grade inflation", "academic standards", "memo"])
    add("Office of Undergraduate Admissions <ugadmit@illinois.example.edu>", ["rao"], "FW: Campus approval - B.S. Sustainable Food Systems",
        "Forwarding for your files.\n\n-----Original Message-----\nFrom: Board of Trustees Office\nSent: Thursday, January 17, 2019\nSubject: Program approval\n\nThe Board approved the B.S. in Sustainable Food Systems, effective Fall 2019.\n\n"
        "-----Original Message-----\nFrom: Senate Educational Policy Committee\nSent: Monday, November 26, 2018\nSubject: SFS proposal\n\nEPC recommends approval of the CAES proposal for a B.S. in Sustainable Food Systems with minor revisions to the policy concentration.",
        d(2019, 1, 18, 10, 0), "high", "Records of program approval (forwarded approval chain)", "Approval chain for the Sustainable Food Systems major",
        "Forwarded chain showing the Senate committee recommending and the Board approving the Sustainable Food Systems B.S. effective Fall 2019.", ["program approval", "Board of Trustees", "forwarded thread"],
        diff="subtle", tags=["email_thread_forwarded"])
    add("hale", ["chairs"], "Reminder: course proposals due Sept 15",
        "Proposals for Spring changes are due September 15 via the curriculum system. Use the 2019 form; old forms will be returned.", d(2019, 8, 20, 9, 0),
        "moderate", "Routine operational correspondence of the office about curriculum process", "Curriculum proposal deadline reminder",
        "Curriculum coordinator reminds departments of the September 15 proposal deadline and required form.", ["deadline", "curriculum"], diff="subtle")
    add("dean", ["rao"], "Annual report due July 15", "Sunita, please send your annual report by July 15 using the college template. Thanks, Patricia", d(2021, 6, 1, 8, 0),
        "low", "Routine request; the report itself is kept", "Dean's request for annual report", "Dean reminds the associate dean of the annual report deadline.", ["annual report", "reminder"], diff="subtle")
    add("kowal", ["rao", "hale"], "Doodle: curriculum retreat", "Please fill in the Doodle for the August retreat: https://doodle.example.com/poll/x7", d(2019, 6, 3, 14, 0),
        "none", "Routine scheduling", "Scheduling poll for retreat", "Office manager circulates a scheduling poll.", ["scheduling"])
    add("Campus Catering <orders@catering.example.edu>", ["kowal"], "Order confirmation #8812 - box lunches x 25", "Your order for 25 box lunches on Aug 14 is confirmed. Total $337.50.", d(2019, 8, 1, 10, 0),
        "none", "Routine transactional records (catering)", "Catering order confirmation", "Catering confirmation for 25 box lunches.", ["catering"], tags=["retention_eligible"])
    add("Facilities Scheduling <rooms@illinois.example.edu>", ["kowal"], "Room 112 reserved: Curriculum Committee Oct 8", "Room 112 is reserved Oct 8, 3-5 pm.", d(2019, 9, 20, 9, 0),
        "none", "Routine room bookings", "Room booking confirmation", "Room reservation confirmation for a committee meeting.", ["room booking"], tags=["retention_eligible"])
    add("Office of Sustainability <green@illinois.example.edu>", ["faculty"], "Green Campus Newsletter - October", "Composting expands to 4 more buildings! Bike to Work Day recap.", d(2021, 10, 2, 7, 0),
        "none", "Newsletters from other units", "Sustainability office newsletter", "Another unit's newsletter about composting and bike to work day.", ["newsletter"], diff="subtle")
    add("IT Security <security-alert@illinois-edu.example.net>", ["kowal"], "Your mailbox is full - verify now", "Your mailbox has exceeded its quota. Click here and log in to avoid deletion.", d(2022, 3, 3, 4, 0),
        "none", "Spam and phishing", "Phishing message about mailbox quota", "Phishing email from a look-alike domain.", ["phishing"], tags=["phishing"])
    add("Student, Kayla Brooks <kbrooks7@illinois.example.edu>", ["rao"], "Petition for late course drop - medical",
        "Dear Dean Rao, I am petitioning to drop AGRON 340 after the deadline. I was hospitalized for two weeks in October (documentation attached separately). UIN 659201844.",
        d(2021, 11, 9, 22, 10), "low", "Individual student records (petitions) belong in the student records system", "Student petition for late drop with medical reason",
        "Student petitions for a late course drop citing hospitalization and gives her ID number.", ["petition", "student record"], sens=("ferpa_student", "medical"))
    add("Dr. Ian Forsythe <iforsythe@caes.illinois.example.edu>", ["whitcomb"], "Academic integrity report - AGRON 340",
        "Reporting a finding for student UIN 653318820 (copied lab report from a former student). Second finding for this student per your office's records. Referral to the Board requested.",
        d(2017, 4, 11, 16, 0), "low", "Academic integrity case records are FERPA-protected student records", "Integrity case report with Board referral",
        "Instructor reports an integrity finding and requests a two-strike Board referral for a named student ID.", ["academic integrity", "case report"], sens=("ferpa_student",), diff="subtle")
    add("Dr. Ruth Alvarez <ralvarez@caes.illinois.example.edu>", ["rao"], "Formal grievance: teaching assignment",
        "I am filing a formal grievance regarding my Fall 2020 assignment to teach AGRON 101 in person despite my documented medical risk. I request reassignment to an online section.",
        d(2020, 7, 28, 13, 0), "moderate", "Shows application of COVID modality policy, but is a confidential personnel grievance", "Faculty grievance over in-person teaching assignment",
        "A faculty member files a formal grievance about an in-person teaching assignment during COVID-19 citing medical risk.", ["grievance", "COVID-19", "personnel"], sens=("hr_personnel", "medical"), diff="ambiguous")
    add("rao", ["Assistant Dean Search Committee <search2019@caes.illinois.example.edu>"], "Candidate rankings - confidential",
        "Committee, my read: Candidate B strongest on assessment experience; Candidate A weak references; Candidate C withdrew. Let's recommend B and A to the Dean in that order.",
        d(2019, 5, 2, 18, 0), "low", "Search committee deliberations are restricted personnel records", "Confidential search committee rankings",
        "Associate dean summarises the committee's ranking of assistant dean candidates.", ["search committee", "personnel"], sens=("hr_personnel",))
    add("kowal", ["rao"], "FY20 salary lines", "Sunita, here are the FY20 lines: Hale $58,400; Kowal $52,100; Mbeki $96,000; student workers $14,200 total.", d(2019, 6, 20, 15, 0),
        "low", "Salary information is restricted; routine budget correspondence", "Office salary lines FY20", "Office manager lists staff salaries for budgeting.",
        ["salary", "budget"], sens=("hr_personnel", "financial_personal"))
    add("kowal", ["Kowal family <kowalfam@mailbox.example.com>"], "Soccer carpool Saturday", "I can drive Saturday, pickup at 8:15. Bring orange slices!", d(2021, 9, 10, 12, 0),
        "none", "Personal files staff left on the share", "Staff personal email about carpool", "Office manager's personal message about a children's soccer carpool.", ["personal"], sens=("minor_child",))
    add("dean", ["faculty"], "Celebrating Leonard Whitcomb", "Please join us June 12 to celebrate Leonard Whitcomb's six years as Associate Dean and his return to the faculty.", d(2018, 5, 30, 9, 0),
        "low", "Routine event announcement; minor record of office leadership change", "Reception for departing associate dean", "Dean invites faculty to celebrate the departing associate dean.", ["event", "leadership transition"], diff="ambiguous")
    for i, (m, rel, why, title, summ, kw, sens, diff, tags) in enumerate(M):
        folder = {"high": "Correspondence/Policy", "moderate": "Correspondence/Operations", "low": "Correspondence/Restricted_and_Routine", "none": "Correspondence/Routine"}[rel]
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in m["Subject"])[:55].strip()
        reg.p(f"{folder}/{i:02d}_{safe}.eml").write_bytes(bytes(m))
        A(f"{folder}/{i:02d}_{safe}.eml", rel, why, lane="email", fmt="message/rfc822", date=m["Date"], title=title, summary=summ, keywords=kw, sens=sens, difficulty=diff, tags=list(tags))
    # Teams export
    msgs = [{"id": f"16{8400000 + i}", "createdDateTime": f"2020-03-{13 + i // 4:02d}T{9 + i % 8:02d}:15:00Z", "from": {"user": {"displayName": who}}, "body": {"content": txt}}
            for i, (who, txt) in enumerate([("Sunita Rao", "Readiness survey link is live - please push to your departments."), ("Marcus Hale", "212 responses already!"),
                                            ("Brenda Kowal", "Who has the key to the copier room?"), ("Sunita Rao", "Labs: we will allow Incompletes. Writing it into the FAQ now."),
                                            ("Marcus Hale", "FAQ v3 posted"), ("Brenda Kowal", "Lunch order for Friday?"), ("Sunita Rao", "Provost agreed to P/NP. Huge."),
                                            ("Marcus Hale", "FAQ v7 is final for now"), ("Brenda Kowal", "Happy birthday Marcus!! 🎂")])]
    reg.p("Teams_Export/ADAP_General_channel_2020-03.json").write_text(json.dumps({"channel": "ADAP > General", "messages": msgs}, indent=1, ensure_ascii=False))
    A("Teams_Export/ADAP_General_channel_2020-03.json", "high", "Records documenting the COVID-19 response (internal coordination chat)", lane="document", fmt="application/json (Teams chat export)",
      date="2020-03-15", title="Teams channel export from the first week of COVID response",
      summary="JSON export of nine Teams messages: survey launch, decision to allow Incompletes for labs, FAQ versions, provost agreeing to Pass/No Pass, mixed with copier-key, lunch and birthday chatter.",
      keywords=["Teams", "chat export", "COVID-19"], tags=["chat_export", "mixed_relevance_within_file"], difficulty="subtle")
    reg.folder("Correspondence", "high", "Saved email sorted by staff into policy, operations, restricted/routine folders.")
    reg.folder("Correspondence/Policy", "high", "Associate dean correspondence that sets or explains policy, COVID-19 guidance, program approval chain.")
    reg.folder("Correspondence/Routine", "none", "Scheduling, catering, room booking, newsletters, phishing.")
    reg.folder("Correspondence/Restricted_and_Routine", "low", "Student petitions and integrity cases (FERPA), search deliberations and salaries (personnel), routine requests.")


# ------------------------------------------------------------------ personnel, finance, events, templates, staff folders, system
def build_rest():
    PS = "Personnel/Search_2019_Assistant_Dean"
    for c, txt in [("A", "Candidate A - CV. PhD Agricultural Education 2010. Assistant Director of Advising 2014-2019."), ("B", "Candidate B - CV. PhD Higher Education 2012. Director of Assessment 2015-2019.")]:
        write_pdf(f"{PS}/Candidate_{c}_CV.pdf", f"Curriculum Vitae - Candidate {c}", [txt, "Home address: 14 Elm St, Urbana (synthetic). Phone (555) 0188."])
        A(f"{PS}/Candidate_{c}_CV.pdf", "low", "Candidate application materials are restricted personnel records", lane="document", fmt="pdf", date="2019-03-01",
          title=f"Search candidate {c} CV", summary=f"Application CV of assistant dean candidate {c} with home contact details.", keywords=["search", "candidate", "CV"], sens=("hr_personnel", "pii_contact"))
    write_xlsx(f"{PS}/committee_scoring_matrix.xlsx", {"Scores": [("Candidate", "Assessment", "Advising", "Leadership", "Total"), ("A", 3, 5, 3, 11), ("B", 5, 4, 4, 13), ("C", 4, 3, 3, 10)]})
    A(f"{PS}/committee_scoring_matrix.xlsx", "low", "Search committee deliberations are restricted", lane="tabular", fmt="xlsx", date="2019-04-28",
      title="Search committee scoring matrix", summary="Scores of three candidates on assessment, advising and leadership.", keywords=["search", "scoring"], sens=("hr_personnel",))
    write_docx("Personnel/Mbeki_offer_letter_2019.docx", "Offer of Appointment", ["Dear Dr. Mbeki, I am pleased to offer you the position of Assistant Dean at an annual salary of $96,000, effective August 16, 2019."])
    A("Personnel/Mbeki_offer_letter_2019.docx", "low", "Personnel record with salary (restricted)", lane="document", fmt="docx", date="2019-05-20",
      title="Offer letter to new assistant dean", summary="Offer letter stating the assistant dean appointment and salary.", keywords=["offer letter", "salary"], sens=("hr_personnel", "financial_personal"))
    F = "Finance"
    for i, (item, amt, y) in enumerate([("Toner cartridges x6", 412.20, 2014), ("Office chairs x2", 690.00, 2016), ("Commencement programs printing", 1840.00, 2017), ("Laptop for coordinator", 1299.00, 2019), ("Name badges", 86.40, 2021)]):
        write_pdf(f"{F}/Purchase_Orders/PO_{y}-{1000 + i * 77}.pdf", f"PURCHASE ORDER {y}-{1000 + i * 77}", [f"Item: {item}", f"Amount: ${amt:,.2f}", "Account: 1-xxxxx-ADAP"])
        A(f"{F}/Purchase_Orders/PO_{y}-{1000 + i * 77}.pdf", "none", "Routine transactional records past retention (purchase orders)", lane="document", fmt="pdf", date=f"{y}-03-01",
          title=f"Purchase order {y}: {item}", summary=f"Purchase order for {item.lower()}.", keywords=["purchase order"], tags=["retention_eligible"])
    for i, (trip, y) in enumerate([("NACTA conference, Logan UT", 2015), ("Assessment Institute, Indianapolis", 2018), ("AAC&U meeting, Washington DC", 2022)]):
        scan(f"{F}/Travel/travel_voucher_{y}_{i}.pdf", [f"Traveler: {'L. Whitcomb' if y < 2018 else 'S. Rao'}", f"Trip: {trip}", "Airfare $412  Lodging $618  Meals $140", "Total $1,170"], "TRAVEL VOUCHER")
        A(f"{F}/Travel/travel_voucher_{y}_{i}.pdf", "none", "Routine transactional records past retention (travel vouchers)", lane="document", fmt="pdf (image-only scan)", date=f"{y}-06-01",
          title=f"Travel voucher {y}", summary=f"Scanned travel voucher for {trip}.", keywords=["travel voucher"], tags=["retention_eligible", "scanned_image_pdf", "needs_ocr"])
    write_xlsx(f"{F}/ADAP_budget_FY20.xlsx", {"Budget": [("Line", "FY20"), ("Salaries - staff", 110500), ("Salaries - student", 14200), ("Assistant Dean", 96000), ("Operations", 22000), ("Curriculum grants to depts", 60000)]})
    A(f"{F}/ADAP_budget_FY20.xlsx", "moderate", "Office budget shows priorities (curriculum grants), but includes salary lines (restricted)", lane="tabular", fmt="xlsx", date="2019-07-01",
      title="Office budget FY20", summary="Office budget with staff and assistant dean salary lines, operations and curriculum grants to departments.", keywords=["budget", "FY20"], sens=("hr_personnel",), difficulty="ambiguous")
    E = "Events"
    write_pdf(f"{E}/Commencement_Program_2019.pdf", "CAES Convocation 2019", ["Processional", "Welcome - Dean Okafor-Grant", "Presentation of graduates: 612 bachelor's degrees", "Recessional"])
    A(f"{E}/Commencement_Program_2019.pdf", "moderate", "Records of college events (ceremony program)", lane="document", fmt="pdf", date="2019-05-11",
      title="College convocation program 2019", summary="Convocation program listing the order of ceremony and 612 bachelor's degrees.", keywords=["commencement", "program"], difficulty="subtle")
    from gen_media import prairie_scene
    for k in range(3):
        im = Image.new("RGB", (1600, 1067), (200, 190, 170)); dr = ImageDraw.Draw(im)
        dr.rectangle([0, 700, 1600, 1067], fill=(120, 30, 40))
        for j in range(9):
            x = 120 + j * 160; dr.ellipse([x, 380, x + 70, 450], fill=(210, 170, 140)); dr.rectangle([x - 10, 450, x + 80, 700], fill=(20, 20, 60))
            dr.polygon([(x - 15, 385), (x + 85, 385), (x + 35, 360)], fill=(10, 10, 10))
        save_jpg(im, f"{E}/Photos_Convocation_2019/DSC_{3301 + k}.JPG", f"2019:05:11 10:{12 + k}:00", make="Nikon", model="D7500")
        A(f"{E}/Photos_Convocation_2019/DSC_{3301 + k}.JPG", "moderate", "Photographs of college events", lane="image", fmt="jpeg (EXIF)", date="2019-05-11",
          title=f"Convocation 2019 photo {k + 1}", summary="Illustration-style photo of graduates in caps and gowns lined up at the 2019 convocation.", keywords=["convocation", "graduates", "photo"],
          action="appraise" if k == 0 else "review_near_duplicate", tags=["near_duplicate"] if k else [], difficulty="subtle")
    with open(reg.p(f"{E}/room_bookings_2018-2022.csv"), "w") as fh:
        fh.write("date,room,event,booked_by\n" + "".join(f"20{18 + i // 10}-0{1 + i % 9}-1{i % 9},Room 112,Committee meeting,BKowal\n" for i in range(40)))
    A(f"{E}/room_bookings_2018-2022.csv", "none", "Routine room bookings", lane="tabular", fmt="text/csv", title="Room booking log 2018-2022", summary="Log of 40 routine room bookings.",
      keywords=["room bookings"], tags=["retention_eligible"])
    T = "Templates"
    write_docx(f"{T}/BLANK_Course_Proposal_Form_2019.docx", "CAES Course Proposal Form (2019)", ["Course number: ____", "Title: ____", "Rationale: ____", "Learning outcomes: ____"])
    A(f"{T}/BLANK_Course_Proposal_Form_2019.docx", "none", "Blank forms and templates", lane="document", fmt="docx", title="Blank course proposal form", summary="Empty course proposal template.", keywords=["template", "blank form"])
    write_docx(f"{T}/ADAP_letterhead.docx", "Office of the Associate Dean for Academic Programs", ["College of Agricultural and Environmental Sciences", "[date]", "[body]"])
    A(f"{T}/ADAP_letterhead.docx", "none", "Letterhead", lane="document", fmt="docx", title="Office letterhead template", summary="Letterhead template with placeholders.", keywords=["letterhead", "template"])
    write_docx(f"{T}/~$AP_letterhead.docx", "", []); reg.p(f"{T}/~$AP_letterhead.docx").write_bytes(b"\x06BKowal" + b"\x00" * 155)
    A(f"{T}/~$AP_letterhead.docx", "none", "Application temporary files", lane="system", fmt="ms-office-lockfile", action="exclude_system_file", title="Word lock file",
      summary="Word owner/lock file.", keywords=["lock file"], tags=["system_file", "lock_file"])
    # staff personal folders
    SF = "Staff_Folders"
    dup("Policies/Academic_Integrity/AI_Policy_FINAL_approved_2016-02.pdf", f"{SF}/Brenda/policies I need/AI_Policy_FINAL_approved_2016-02.pdf")
    dup("Policies/Academic_Integrity/AI_Policy_FINAL_approved_2016-02.pdf", "Curriculum_Committee/2015-2016/AI_Policy_FINAL_approved_2016-02.pdf")
    dup("Policies/Grade_Appeals/Grade_Appeal_Procedure_2018_FINAL.docx", f"{SF}/Marcus/Grade_Appeal_Procedure_2018_FINAL.docx")
    write_docx(f"{SF}/Brenda/my_resume_2023.docx", "Brenda Kowal", ["Office Manager, CAES 2011-2024", "Skills: budgeting, event planning, Banner, Concur"])
    A(f"{SF}/Brenda/my_resume_2023.docx", "none", "Personal files staff left on the share", lane="document", fmt="docx", title="Staff member's personal resume", summary="Office manager's personal resume.",
      keywords=["resume", "personal"], sens=("pii_contact",), difficulty="subtle")
    save_jpg(prairie_scene(77, w=1200, h=800, sky=(120, 180, 240)), f"{SF}/Brenda/vacation/IMG_2201.jpg", "2022:07:04 15:00:00", make="Apple", model="iPhone 12")
    A(f"{SF}/Brenda/vacation/IMG_2201.jpg", "none", "Personal files staff left on the share", lane="image", fmt="jpeg", title="Staff vacation photo", summary="Personal vacation landscape photo.",
      keywords=["personal photo"], difficulty="obvious")
    reg.p(f"{SF}/Marcus/curric_mtg_notes_2021-10.txt").write_text(
        "Oct 2021 curric mtg - my notes\n- NRES 310 online: Rao says permanent, but faculty split 5-3\n- ACES 101 retire? DEFERRED, Dean wants data first\n- SFS first-year review next spring\n")
    A(f"{SF}/Marcus/curric_mtg_notes_2021-10.txt", "moderate", "Staff working notes adding detail (vote split) not in the official minutes", lane="document", fmt="text/plain", date="2021-10-08",
      title="Curriculum coordinator's personal meeting notes", summary="Coordinator's notes from the October 2021 committee meeting recording a 5-3 faculty split on the NRES 310 online decision, detail absent from the minutes.",
      keywords=["meeting notes", "curriculum committee"], difficulty="ambiguous")
    write_xlsx(f"{SF}/Marcus/course_inventory_WORKING.xlsx", {"Courses": [("Course", "Last offered", "Status", "Note")] + [(f"AGRON {n}", f"FA{18 + n % 5}", s, nt) for n, s, nt in [(101, "active", ""), (199, "special topics", "check"), (340, "active", "prereq changed 2016"), (450, "dormant", "propose deletion?")]]})
    A(f"{SF}/Marcus/course_inventory_WORKING.xlsx", "moderate", "Working data on the curriculum, unofficial", lane="tabular", fmt="xlsx", date="2021-11-01",
      title="Working course inventory", summary="Coordinator's working list of courses with last-offered terms and status notes, including a dormant course proposed for deletion.",
      keywords=["course inventory", "working file"], difficulty="ambiguous")
    reg.p(f"{SF}/Marcus/Thumbs.db").write_bytes(bytes.fromhex("D0CF11E0A1B11AE1") + b"\x00" * 2040)
    A(f"{SF}/Marcus/Thumbs.db", "none", "Operating-system files", lane="system", fmt="Windows thumbnail cache", action="exclude_system_file", title="Windows thumbnail cache",
      summary="Windows thumbnail cache.", keywords=["system file"], tags=["system_file"])
    reg.p("desktop.ini").write_bytes("[.ShellClassInfo]\r\nIconResource=C:\\Windows\\System32\\imageres.dll,-1023\r\n".encode("utf-16"))
    A("desktop.ini", "none", "Operating-system files", lane="system", fmt="Windows desktop.ini", action="exclude_system_file", title="Windows folder settings", summary="Windows folder settings file.",
      keywords=["system file"], tags=["system_file"])
    reg.p("Annual_Reports/~WRL0004.tmp").write_bytes(bytes(rng("wrl").randrange(256) for _ in range(5000)))
    A("Annual_Reports/~WRL0004.tmp", "none", "Application temporary files", lane="system", fmt="Word temporary file", action="exclude_system_file", title="Word temporary file",
      summary="Leftover Word temp file.", keywords=["temp file"], tags=["system_file"])
    reg.p("Policies/.849C9593-D756-4E56-8D6E-42412F2A707B").write_bytes(b"")
    A("Policies/.849C9593-D756-4E56-8D6E-42412F2A707B", "none", "Synchronisation system file", lane="system", fmt="empty (OneDrive sync marker)", action="exclude_system_file",
      title="OneDrive sync marker", summary="Zero-byte hidden OneDrive synchronisation marker.", keywords=["sync", "system file"], tags=["system_file", "zero_byte", "hidden_file"])
    reg.folder("Personnel", "low", "Restricted personnel records: search materials and an offer letter.")
    reg.folder("Finance", "none", "Purchase orders and travel vouchers past retention, plus an office budget with salary lines.")
    reg.folder("Events", "moderate", "Convocation program and photos (near-duplicates), routine room-booking log.")
    reg.folder("Templates", "none", "Blank forms, letterhead and a lock file.")
    reg.folder(SF, "low", "Staff personal folders: duplicate policies, personal resume and photo, coordinator's working notes and course inventory.")
    reg.folder("Website_Content", "low", "Saved web copies of policies.")


def run():
    build_policies(); build_curriculum(); build_reviews_plans(); build_covid_data(); build_mail(); build_rest()
