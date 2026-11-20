"""Document lane: PDF (text, mixed-media, scanned, encrypted), Office (modern+legacy),
text formats, slides and spreadsheets."""
from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
from pathlib import Path

import docx
from docx.shared import Inches, Pt
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.comments import Comment
from pptx import Presentation
from pptx.util import Inches as PInches, Pt as PPt
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table,
                                TableStyle, PageBreak)
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib import pdfencrypt
from PIL import Image as PILImage, ImageDraw, ImageFont, ImageFilter

import charts
import texts as T
from common import reg, rng, SITES, GRANT, GRANT_TITLE, DONOR, ROOT
from survey import richness_table

SS = getSampleStyleSheet()
SMALL = ParagraphStyle("small", parent=SS["BodyText"], fontSize=8, leading=10)

R = "Documents/Research"
PBS = f"{R}/Prairie_Bee_Survey"
MS = f"{R}/Manuscripts/2021_JPE_restoration_age"


def img(png_bytes, width=4.8 * inch):
    ir = ImageReader(io.BytesIO(png_bytes))
    w, h = ir.getSize()
    return Image(io.BytesIO(png_bytes), width=width, height=width * h / w)


def pdf_doc(rel, story, title="", author="", encrypt=None):
    path = reg.p(rel)
    kw = {}
    if encrypt:
        kw["encrypt"] = encrypt
    doc = SimpleDocTemplate(str(path), pagesize=letter, title=title, author=author,
                            leftMargin=0.8 * inch, rightMargin=0.8 * inch, **kw)
    doc.build(story)
    return path


def soffice(src: Path, fmt: str, outdir: Path) -> Path:
    subprocess.run(["soffice", "--headless", "--convert-to", fmt, "--outdir", str(outdir), str(src)],
                   check=True, capture_output=True, timeout=180)
    return outdir / (src.stem + "." + fmt.split(":")[0])


# ------------------------------------------------------------------ manuscripts
def manuscript_docx(version, rel, extra_note=None, with_figs=True):
    d = docx.Document()
    cp = d.core_properties
    cp.author, cp.title = DONOR, T.MS_TITLE
    d.add_heading(T.MS_TITLE, 0)
    d.add_paragraph(T.MS_AUTHORS).italic = True
    if extra_note:
        p = d.add_paragraph(); r = p.add_run(extra_note); r.bold = True
    d.add_heading("Abstract", 1)
    abstract = T.ABSTRACT if version >= 3 else T.ABSTRACT.replace(
        "Specialist richness was positively associated with bare-ground cover at trap stations, "
        "suggesting that nesting substrate, not floral resources, limits their recovery. ", "")
    d.add_paragraph(abstract)
    for head, paras in [("Introduction", T.INTRO), ("Methods", T.METHODS),
                        ("Results", T.RESULTS[: 2 if version < 3 else 3]),
                        ("Discussion", T.DISCUSSION[: version])]:
        d.add_heading(head, 1)
        for p in paras:
            d.add_paragraph(p)
    if with_figs:
        d.add_heading("Figures", 1)
        d.add_picture(io.BytesIO(charts.richness_vs_age()), width=Inches(5))
        d.add_paragraph("Figure 1. Total bee richness against years since restoration.")
        d.add_picture(io.BytesIO(charts.richness_vs_age(specialists=True)), width=Inches(5))
        d.add_paragraph("Figure 2. Ground-nesting specialist richness.")
    d.save(reg.p(rel))


def build_manuscripts():
    notes = {1: "DRAFT v1 - for Rafael only", 2: "DRAFT v2 - RQ edits accepted",
             3: "v3 - SUBMITTED to JPE 2020-06-30", 4: "v4 - REVISION after reviews, Fig S4 added"}
    for v in (1, 2, 3, 4):
        rel = f"{MS}/drafts/Achterberg_restoration_age_v{v}.docx"
        manuscript_docx(v, rel, notes[v])
        reg.add(rel, "high", "Drafts of manuscripts that show how the papers changed",
                lane="document", fmt="docx", date=["2020-03-10", "2020-05-02", "2020-06-30", "2020-11-20"][v - 1],
                title=f"Restoration-age manuscript, draft version {v}",
                summary=f"Version {v} of the manuscript on native bee recovery after prairie restoration ({notes[v]}); "
                        f"contains abstract, methods, results and embedded figures of richness against restoration age."
                        + (" Adds bare-ground result and remnant sensitivity analysis." if v >= 3 else ""),
                keywords=["manuscript draft", "restoration age", "bee richness", f"version {v}"],
                difficulty="obvious" if v in (1, 4) else "subtle",
                tags=["near_duplicate_text", "version_series"])
    # Word lock file left behind
    lock = reg.p(f"{MS}/drafts/~$hterberg_restoration_age_v4.docx")
    lock.write_bytes(b"\x0cM. Achterberg" + b"\x00" * 149)
    reg.add(f"{MS}/drafts/~$hterberg_restoration_age_v4.docx", "none",
            "Operating-system and application temporary files", lane="system",
            action="exclude_system_file", fmt="ms-office-lockfile", title="Word owner/lock file",
            summary="162-byte Microsoft Word owner file left when the v4 draft was open; contains only the user name.",
            keywords=["lock file", "temporary"], tags=["system_file", "lock_file"])

    # Response to reviewers
    d = docx.Document()
    d.add_heading("Response to reviewers - JPE-2020-0388", 0)
    for q, a in T.RESPONSE_TO_REVIEWERS:
        p = d.add_paragraph(); p.add_run(q).bold = True
        d.add_paragraph(a)
    rel = f"{MS}/review/Response_to_Reviewers_JPE-2020-0388.docx"
    d.save(reg.p(rel))
    reg.add(rel, "high", "Reviewer correspondence and response letters that show how the papers changed",
            lane="document", fmt="docx", date="2020-11-20",
            title="Point-by-point response to reviewers for JPE-2020-0388",
            summary="Authors' response addressing dependence on the remnant site (new Fig. S4), the trapping-effort offset correction, floral density versus bare ground, and generalised deposit of rusty patched bumble bee locations.",
            keywords=["response to reviewers", "revision", "sensitivity analysis"])

    # Published article PDF (mixed media: text + figures + table)
    story = [Paragraph("Journal of Pollination Ecology 14: 211-229 (2021) - SYNTHETIC", SMALL),
             Paragraph(T.MS_TITLE, SS["Title"]), Paragraph(T.MS_AUTHORS, SS["Italic"]),
             Spacer(1, 8), Paragraph("<b>Abstract.</b> " + T.ABSTRACT, SS["BodyText"])]
    for head, paras in [("Introduction", T.INTRO), ("Methods", T.METHODS)]:
        story.append(Paragraph(head, SS["Heading2"]))
        story += [Paragraph(p, SS["BodyText"]) for p in paras]
    story.append(Paragraph("Results", SS["Heading2"]))
    story.append(Paragraph(T.RESULTS[0], SS["BodyText"]))
    story.append(img(charts.richness_vs_age()))
    story.append(Paragraph("Figure 1. Total richness saturates about ten years after restoration.", SMALL))
    story.append(Paragraph(T.RESULTS[1], SS["BodyText"]))
    story.append(img(charts.richness_vs_age(specialists=True)))
    story.append(Paragraph("Figure 2. Specialists continue to accumulate; star = remnant.", SMALL))
    rows = [["Site", "Restored", "Mean richness", "Mean specialists"]]
    for code, name, *_ in SITES:
        rt = [r for r in richness_table() if r[0] == code]
        rows.append([code if code != "BRF" else "Remnant*", "remnant" if code == "BRF" else str([s for s in SITES if s[0] == code][0][3]),
                     f"{sum(r[3] for r in rt) / len(rt):.1f}", f"{sum(r[4] for r in rt) / len(rt):.1f}"])
    t = Table(rows); t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .3, colors.grey),
                                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                            ("FONTSIZE", (0, 0), (-1, -1), 8)]))
    story += [Spacer(1, 6), t, Paragraph("*Location withheld (federally listed species).", SMALL),
              Paragraph(T.RESULTS[2], SS["BodyText"]), Paragraph("Discussion", SS["Heading2"])]
    story += [Paragraph(p, SS["BodyText"]) for p in T.DISCUSSION]
    rel = f"{MS}/published/Achterberg_etal_2021_JPE.pdf"
    pdf_doc(rel, story, T.MS_TITLE, DONOR)
    reg.add(rel, "high", "Published results of the Prairie Bee Survey with the figures the analysis generated",
            lane="document", fmt="pdf (text + raster figures + table)", date="2021-04-15",
            title="Achterberg et al. 2021, native bee recovery after prairie restoration (published)",
            summary="Published multi-page article reporting 20,937 bees across a restoration chronosequence: total richness saturates after about ten years while ground-nesting specialists lag; bare ground predicts specialist richness. Includes two figures and a site table with the remnant location withheld.",
            keywords=["publication", "pollinators", "chronosequence", "prairie restoration", "specialist bees"],
            tags=["mixed_media_pdf", "charts_in_pdf", "table_in_pdf"])

    # LaTeX source + bibliography for the same paper
    tex = "\\documentclass{article}\n\\title{" + T.MS_TITLE + "}\n\\author{" + T.MS_AUTHORS + "}\n" \
          "\\begin{document}\\maketitle\n\\begin{abstract}" + T.ABSTRACT + "\\end{abstract}\n" + \
          "\\section{Introduction}\n" + "\n\n".join(T.INTRO) + " \\cite{winfree2009,kremen2002}\n" + \
          "\\section{Methods}\n" + "\n\n".join(T.METHODS) + "\n\\bibliographystyle{apalike}\n\\bibliography{refs}\n\\end{document}\n"
    reg.p(f"{MS}/latex/main.tex").write_text(tex)
    reg.add(f"{MS}/latex/main.tex", "high", "Drafts of manuscripts (LaTeX source)", lane="code", fmt="text/x-tex",
            title="LaTeX source of the restoration-age manuscript",
            summary="LaTeX source for the manuscript including title, abstract, introduction and methods with citation keys.",
            keywords=["LaTeX", "manuscript source"], date="2020-06-28", difficulty="subtle")
    bib = """@article{winfree2009,
  title={A meta-analysis of bees' responses to anthropogenic disturbance},
  author={Winfree, R. and Aguilar, R. and Vazquez, D. P. and LeBuhn, G. and Aizen, M. A.},
  journal={Ecology}, year={2009}, note={Real reference; annotation: key framing for disturbance}
}
@article{kremen2002,
  title={Crop pollination from native bees at risk from agricultural intensification},
  author={Kremen, C. and Williams, N. M. and Thorp, R. W.},
  journal={PNAS}, year={2002}
}
@article{quintero2018,
  title={Offsets for unequal trapping effort in bee surveys (SYNTHETIC)},
  author={Quintero, R.}, journal={Methods in Synthetic Ecology}, year={2018}
}
"""
    reg.p(f"{MS}/latex/refs.bib").write_text(bib)
    reg.add(f"{MS}/latex/refs.bib", "moderate", "Bibliography supporting the manuscript drafts", lane="code",
            fmt="text/x-bibtex", title="BibTeX references for the manuscript",
            summary="BibTeX file with three references cited by the manuscript, including a note on how one source framed the argument.",
            keywords=["bibliography", "BibTeX", "citations"], difficulty="subtle")

    reg.folder(f"{R}/Manuscripts", "high", "Manuscript drafts, reviews, LaTeX sources and published versions of Prairie Bee Survey papers.")
    reg.folder(MS, "high", "Complete paper trail for the 2021 restoration-age article: four drafts, review response, LaTeX, published PDF.")


# ------------------------------------------------------------------ grants
def build_grants():
    G = f"{R}/Grants/NSF_DEB-1900417"
    story = [Paragraph(f"{GRANT} - Project Summary (SYNTHETIC)", SS["Title"]),
             Paragraph(GRANT_TITLE, SS["Heading2"]), Paragraph(T.PROPOSAL_SUMMARY, SS["BodyText"]),
             PageBreak(), Paragraph("Project Description", SS["Heading1"]),
             Paragraph("1. Preliminary results", SS["Heading2"]),
             Paragraph("Pilot surveys in 2016-2018 at ten sites show steep early gains in bee richness. "
                       "Figure 1 shows pilot richness by site age; the remnant is starred.", SS["BodyText"]),
             img(charts.richness_vs_age(title="Pilot data 2016-2018")),
             Paragraph("2. Site map", SS["Heading2"]), img(charts.site_map(), 3.6 * inch),
             Paragraph("3. Budget justification", SS["Heading2"]), img(charts.budget_pie(), 3.2 * inch),
             Paragraph("4. Data management plan", SS["Heading2"])] + \
            [Paragraph(p, SS["BodyText"]) for p in T.DMP]
    rel = f"{G}/proposal/DEB-1900417_full_proposal.pdf"
    pdf_doc(rel, story, GRANT_TITLE, DONOR)
    reg.add(rel, "high", "Grant proposals and data-management plans for the NSF award", lane="document",
            fmt="pdf (text + charts + map)", date="2018-08-01",
            title="NSF DEB-1900417 full proposal: bee recovery across a prairie restoration chronosequence",
            summary="Full NSF proposal with project summary, preliminary pilot results figure, survey site map (including exact remnant location), budget pie chart and data-management plan committing to generalise endangered-species locations.",
            keywords=["NSF", "grant proposal", "data management plan", "chronosequence", "site map"],
            sens=("sensitive_location",), tags=["mixed_media_pdf", "charts_in_pdf", "map_in_pdf"])

    # annual reports (docx), DMP (md)
    for yr in (2020, 2021, 2022):
        d = docx.Document()
        d.add_heading(f"{GRANT} Annual Project Report - Year {yr - 2019}", 0)
        d.add_paragraph(f"Reporting period: Sept {yr - 1} - Aug {yr}.")
        d.add_heading("Accomplishments", 1)
        d.add_paragraph({2020: "Completed 2019 field season at all ten sites; 3,120 specimens curated; first B. affinis records at the remnant.",
                         2021: "Published restoration-age paper in JPE; barcoded 640 Lasioglossum; presented to Illinois Pollinator Working Group.",
                         2022: "Final field season; bare-ground experiment at two sites; Natarajan dissertation chapters 2-3 drafted."}[yr])
        d.add_heading("Training and broader impacts", 1)
        d.add_paragraph("Two PhD and two MS students trained; three landowner field days held.")
        rel = f"{G}/reports/Annual_Report_Y{yr - 2019}_{yr}.docx"
        d.save(reg.p(rel))
        reg.add(rel, "high", "Progress reports for the NSF award", lane="document", fmt="docx", date=f"{yr}-08-30",
                title=f"NSF annual project report, year {yr - 2019}",
                summary=f"Annual report to NSF for {yr - 1}-{yr} listing field, publication, training and outreach accomplishments.",
                keywords=["annual report", "NSF", "accomplishments"])
    dmp = "# Data Management Plan - " + GRANT + "\n\n" + "\n\n".join(f"- {p}" for p in T.DMP) + "\n"
    reg.p(f"{G}/proposal/DMP.md").write_text(dmp)
    reg.add(f"{G}/proposal/DMP.md", "high", "Data-management plans for the NSF award", lane="document",
            fmt="text/markdown", date="2018-07-25", title="Data management plan (Markdown)",
            summary="Markdown data-management plan listing data types, Darwin Core and FGDC standards, repository deposit, and county-level generalisation for listed species.",
            keywords=["data management plan", "Darwin Core", "metadata standards"])

    # Budget workbook with embedded chart image & comment
    wb = Workbook(); ws = wb.active; ws.title = "Budget"
    ws.append(["Category", "Y1", "Y2", "Y3", "Y4", "Total"])
    for cat, vals in [("Senior personnel", [18, 18, 19, 19]), ("Graduate students", [34, 35, 36, 37]),
                      ("Fringe", [22, 23, 25, 26]), ("Field travel", [16, 15, 16, 14]),
                      ("DNA barcoding", [12, 10, 9, 7]), ("Supplies", [8, 7, 6, 6])]:
        ws.append([cat] + vals + [f"=SUM(B{ws.max_row + 1}:E{ws.max_row + 1})"])
    ws["A9"] = "All values in $K. Indirect costs excluded."
    ws["F3"].comment = Comment("Assumes 2 RAs at 50% from Y2", "MKA")
    ws2 = wb.create_sheet("Chart"); ws2.add_image(XLImage(io.BytesIO(charts.budget_pie())), "A1")
    rel = f"{G}/proposal/DEB-1900417_budget_FINAL_v3.xlsx"
    wb.save(reg.p(rel))
    reg.add(rel, "high", "Grant proposals (budget component)", lane="tabular", fmt="xlsx (formulas, comment, embedded image)",
            date="2018-07-30", title="NSF proposal budget workbook",
            summary="Four-year budget by category in thousands of dollars with SUM formulas, a reviewer comment and a second sheet holding a budget pie chart image.",
            keywords=["budget", "NSF", "spreadsheet"], tags=["formulas", "embedded_image"], difficulty="subtle")
    reg.folder(f"{R}/Grants", "high", "NSF award DEB-1900417: proposal, budget, data-management plan and annual reports.")


# ------------------------------------------------------------------ literature
def build_literature():
    L = f"{R}/Literature"
    papers = [
        ("Winfree_2009_meta-analysis_disturbance.pdf", "A meta-analysis of bees' responses to anthropogenic disturbance (reprint, SYNTHETIC TEXT)", True),
        ("Kremen_2002_PNAS_crop_pollination.pdf", "Crop pollination from native bees at risk from agricultural intensification (reprint, SYNTHETIC TEXT)", False),
        ("Harmon-Threatt_2016_restoration_review.pdf", "Bees in restored habitats: a review (reprint, SYNTHETIC TEXT)", True),
        ("Smith_2019_soybean_aphid.pdf", "Soybean aphid resistance in commercial cultivars (reprint, SYNTHETIC TEXT)", False),
    ]
    for fname, title, annotated in papers:
        path = reg.p(f"{L}/{fname}")
        c = canvas.Canvas(str(path), pagesize=letter)
        c.setFont("Times-Bold", 14); c.drawString(72, 720, title[:80])
        c.setFont("Times-Roman", 10)
        y = 690
        body = ("This placeholder reprint stands in for a published article by other authors. "
                "Its text is synthetic; the real article is available from the publisher. ") * 6
        for i in range(0, len(body), 95):
            c.drawString(72, y, body[i:i + 95]); y -= 13
        if annotated:
            c.setFillColorRGB(.85, .1, .1); c.setFont("Helvetica-Oblique", 11)
            c.drawString(330, 560, "MKA: use this for framing para 2 -")
            c.drawString(330, 546, "but they ignore nesting guilds!")
            c.setStrokeColorRGB(.95, .85, .1); c.setLineWidth(9)
            c.line(72, 663, 400, 663)
            c.setFillColorRGB(1, 1, .6); c.rect(430, 700, 120, 60, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0); c.setFont("Helvetica", 8)
            c.drawString(435, 745, "Sticky note: compare"); c.drawString(435, 733, "with our remnant data")
        c.showPage(); c.save()
        rel = f"{L}/{fname}"
        if "aphid" in fname:
            reg.add(rel, "none", "Unannotated article by other authors, available from publisher, unrelated topic (crop pest)",
                    lane="document", fmt="pdf", title=title, summary="Unannotated reprint of an article on soybean aphid resistance in crops, outside the survey's subject.",
                    keywords=["soybean aphid", "crop pest", "reprint"], difficulty="subtle")
        elif annotated:
            reg.add(rel, "moderate", "Her own annotated copies of literature, where her notes show how she used the source",
                    lane="document", fmt="pdf (with annotations)", title=title,
                    summary="Reprint of another author's article bearing Achterberg's handwritten-style margin note, highlight and sticky note relating it to nesting guilds and the remnant data.",
                    keywords=["literature", "annotated", "reprint", "pollinators"], difficulty="ambiguous",
                    tags=["annotated_pdf"])
        else:
            reg.add(rel, "low", "Unannotated copies of published articles by other authors (excluded) though on-topic",
                    lane="document", fmt="pdf", title=title,
                    summary="Unannotated reprint of a published pollinator article by other authors; on topic but available from the publisher.",
                    keywords=["literature", "reprint", "pollinators"], difficulty="ambiguous")
    ris = "\n".join(f"TY  - JOUR\nTI  - {t}\nPY  - {fn.split('_')[1]}\nER  - \n" for fn, t, _ in papers)
    reg.p(f"{L}/zotero_export.ris").write_text(ris)
    reg.add(f"{L}/zotero_export.ris", "low", "Reference-manager export of other authors' literature", lane="document",
            fmt="application/x-research-info-systems", title="Zotero RIS export of literature folder",
            summary="RIS citation export listing the four reprints in the literature folder.",
            keywords=["RIS", "citations", "reference manager"], difficulty="ambiguous")
    reg.folder(L, "moderate", "Downloaded reprints by other authors: two carry her annotations, one is off-topic, plus a citation export.")


# ------------------------------------------------------------------ scanned field notebook
def handwriting_page(lines, seed, size=(1700, 2200)):
    r = rng(f"hand{seed}")
    im = PILImage.new("L", size, 238)
    dr = ImageDraw.Draw(im)
    for y in range(160, size[1], 64):
        dr.line([(80, y), (size[0] - 60, y)], fill=200, width=2)
    dr.line([(200, 0), (200, size[1])], fill=215, width=3)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 40)
    except OSError:
        font = ImageFont.load_default()
    y = 110
    for ln in lines:
        x = 220 + r.randint(-6, 6)
        dr.text((x, y + r.randint(-4, 4)), ln, fill=45 + r.randint(0, 30), font=font)
        y += 64
    im = im.rotate(r.uniform(-1.6, 1.6), fillcolor=230, resample=PILImage.BICUBIC)
    noise = PILImage.effect_noise(size, 18).convert("L")
    im = PILImage.blend(im, noise, 0.08).filter(ImageFilter.GaussianBlur(0.8))
    return im


NOTEBOOK_PAGES = [
    ["15 June 2019  BRF (Ritter)  sunny 24C wind 1-2", "set 45 bowls by 8:20, N fence line stations 1-3",
     "10:40 B. affinis worker on Monarda - netted, photo, released",
     "  rusty patch on T2 clear. waypoint BRF-07", "Harold out - talked about burning since 1975",
     "Andrena sp. x3 on Penstemon, Calliopsis on Dalea", "2 bowls tipped st.2 (yellow, white)",
     "bare ground high on N slope after Apr burn"],
    ["16 June 2019  SBP  overcast 21C", "bowls set 8:45. cattle got thru fence on E side?",
     "Bombus griseocollis many, impatiens many", "no specialists netted in 20 min",
     "thatch thick - no burn since 2015", "-> ask DNR about burn schedule", "Priya collected quadrats 1-6"],
    ["17 June 2019  LAF (new planting)", "mostly Halictus, Augochlorella, Apis",
     "very little in bloom - Rudbeckia only", "1 Melissodes (bimaculatus?) blue bowl",
     "weedy, foxtail. 3rd year since seeding", "photo series LAF_T1_N.jpg ..."],
]


def build_field_notebook():
    pages = [handwriting_page(p, i) for i, p in enumerate(NOTEBOOK_PAGES)]
    rel = f"{PBS}/field_notebooks/Field_Notebook_2019_vol2_scan.pdf"
    pages[0].convert("RGB").save(reg.p(rel), "PDF", resolution=200, save_all=True,
                                 append_images=[p.convert("RGB") for p in pages[1:]])
    reg.add(rel, "high", "Field notebooks", lane="document", fmt="pdf (image-only scan, no text layer)",
            date="2019-06-15", title="Scanned field notebook, June 2019 (BRF, SBP, LAF)",
            summary="Three-page image-only scan of handwritten field notes from 15-17 June 2019: rusty patched bumble bee netted at the Ritter remnant (waypoint BRF-07), specialist bees, tipped bowls, burn history and thatch observations at SBP, sparse bloom at the new LAF planting.",
            keywords=["field notebook", "handwritten", "Bombus affinis", "OCR"], sens=("sensitive_location",),
            tags=["scanned_image_pdf", "needs_ocr", "handwriting"])
    # multipage TIFF of same notebook (scanner output)
    rel2 = f"{PBS}/field_notebooks/raw_scans/00361-00363"
    pages[0].save(reg.p(rel2), "TIFF", save_all=True, append_images=pages[1:], compression="tiff_lzw")
    reg.add(rel2, "high", "Field notebooks (raw scanner output)", lane="image", fmt="tiff (multi-page, no extension)",
            date="2019-06-20", title="Raw multi-page TIFF scan of field notebook pages",
            summary="Extensionless batch-numbered scanner output: three-page LZW TIFF of the same June 2019 field notebook pages as the PDF.",
            keywords=["scan", "TIFF", "field notebook"], sens=("sensitive_location",),
            tags=["no_extension", "batch_label_name", "multi_page_tiff", "needs_ocr"], difficulty="subtle")
    reg.folder(f"{PBS}/field_notebooks", "high", "Scanned handwritten field notebooks (PDF and raw TIFF scanner output).")


# ------------------------------------------------------------------ slides
def build_slides():
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[0])
    s.shapes.title.text = "Thirty years of prairie restoration through the eyes of a bee"
    s.placeholders[1].text = "Miriam Achterberg - Departmental seminar, Oct 14 2020"
    for title, png, note in [("Richness recovers fast", charts.richness_vs_age(), "Pause here - point out the remnant star."),
                             ("...but specialists lag", charts.richness_vs_age(specialists=True), "This is the slide DNR cares about."),
                             ("Where we work", charts.site_map(exact_brf=False), "BRF intentionally not shown."),
                             ("What we caught", charts.taxa_bar(), "")]:
        sl = prs.slides.add_slide(prs.slide_layouts[5]); sl.shapes.title.text = title
        sl.shapes.add_picture(io.BytesIO(png), PInches(1.5), PInches(1.6), width=PInches(7))
        if note:
            sl.notes_slide.notes_text_frame.text = note
    sl = prs.slides.add_slide(prs.slide_layouts[1]); sl.shapes.title.text = "Management implications"
    sl.placeholders[1].text = "Burn more often\nKeep bare ground\nProtect remnants - they are the reference"
    rel = "Documents/Talks/2020-10-14_Dept_Seminar_prairie_bees.pptx"
    prs.save(reg.p(rel))
    reg.add(rel, "high", "Slides and talks presenting the research", lane="document", fmt="pptx (images, speaker notes)",
            date="2020-10-14", title="Departmental seminar slides on prairie restoration and bees",
            summary="Seven-slide seminar deck with richness and specialist charts, a site map withholding the remnant, taxa bar chart, management implications and speaker notes.",
            keywords=["seminar", "slides", "management", "pollinators"], tags=["speaker_notes", "charts_in_slides"])
    # garden club outreach talk (moderate)
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[0]); s.shapes.title.text = "Bees in Your Backyard"
    s.placeholders[1].text = "Champaign Garden Club, March 2018"
    sl = prs.slides.add_slide(prs.slide_layouts[1]); sl.shapes.title.text = "Plant these"
    sl.placeholders[1].text = "Wild bergamot\nPurple prairie clover\nGolden Alexanders\nNo-mow patches = nest sites"
    rel = "Documents/Talks/2018_garden_club_bees_in_your_backyard.pptx"
    prs.save(reg.p(rel))
    reg.add(rel, "moderate", "Talks presenting the research (general-audience outreach)", lane="document", fmt="pptx",
            date="2018-03-08", title="Garden club outreach talk on backyard bees",
            summary="Short general-audience slide deck recommending native plants and no-mow patches for bees.",
            keywords=["outreach", "garden club", "native plants"], difficulty="subtle")
    # Legacy .ppt via LibreOffice
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "2007_lab_meeting_bombus_pilot.pptx"
        prs = Presentation()
        s = prs.slides.add_slide(prs.slide_layouts[1]); s.shapes.title.text = "Bombus pilot 2007"
        s.placeholders[1].text = "Netted 6 sites in Champaign Co.\nB. affinis: none\nNeed pan traps next year"
        prs.save(src)
        out = soffice(src, "ppt", Path(td))
        rel = "Old_Computer_Backup_2009/My Documents/lab meetings/bombus pilot 2007.ppt"
        shutil.copy(out, reg.p(rel))
    reg.add(rel, "high", "Records documenting the lab's history; earliest pilot of the survey", lane="document",
            fmt="ppt (legacy OLE2 PowerPoint 97-2003)", date="2007-09-12",
            title="2007 lab meeting slides on Bombus pilot netting",
            summary="Legacy PowerPoint slide from 2007 summarising a bumble bee netting pilot at six Champaign County sites with no rusty patched records and a plan to start pan trapping.",
            keywords=["pilot", "Bombus", "legacy format", "lab history"], tags=["legacy_format"], difficulty="subtle")
    reg.folder("Documents/Talks", "high", "Slide decks: departmental seminar on the survey and a garden-club outreach talk.")


# ------------------------------------------------------------------ CV, admin, teaching, personal
def build_admin_personal():
    # CV docx + pdf
    d = docx.Document(); d.add_heading("Miriam K. Achterberg - Curriculum Vitae", 0)
    for h, items in [("Appointments", ["2018-2024 Professor of Entomology", "2012-2018 Associate Professor", "2006-2012 Assistant Professor"]),
                     ("Grants", [f"{GRANT} (2019-2023), $642,000, PI", "State Wildlife Grant (2016-2018), $88,000, PI"]),
                     ("Selected publications", ["Achterberg MK, Quintero R, Natarajan P, Feld J (2021) " + T.MS_TITLE + ". J Pollination Ecol 14:211-229."]),
                     ("Students advised", ["P. Natarajan (PhD 2023)", "J. Feld (MS 2021)", "+ 4 PhD, 7 MS"])]:
        d.add_heading(h, 1)
        for it in items:
            d.add_paragraph(it, style="List Bullet")
    rel = "Documents/CV/Achterberg_CV_2024.docx"; d.save(reg.p(rel))
    reg.add(rel, "high", "Her curriculum vitae and records documenting her career", lane="document", fmt="docx", date="2024-05-01",
            title="Achterberg curriculum vitae 2024", summary="CV listing appointments 2006-2024, NSF and state grants, the 2021 publication and advised students.",
            keywords=["curriculum vitae", "career", "appointments"])
    with tempfile.TemporaryDirectory() as td:
        out = soffice(reg.p(rel), "pdf", Path(td))
        shutil.copy(out, reg.p("Desktop/Achterberg_CV_2024.pdf"))
    reg.add("Desktop/Achterberg_CV_2024.pdf", "high", "Her curriculum vitae (PDF rendering of the same CV)", lane="document", fmt="pdf",
            date="2024-05-01", title="Achterberg curriculum vitae 2024 (PDF)",
            summary="PDF export of the 2024 CV; same content as the Word version in Documents/CV.",
            keywords=["curriculum vitae", "PDF"], tags=["same_content_different_format"], difficulty="subtle")

    # Peer review she wrote: confidential
    reg.p("Documents/Service/Reviews/ECOAPP-2021-1172_review_MKA.txt").write_text(T.PEER_REVIEW_SHE_WROTE)
    reg.add("Documents/Service/Reviews/ECOAPP-2021-1172_review_MKA.txt", "low",
            "Peer reviews she wrote of other authors' unpublished manuscripts are confidential", lane="document",
            fmt="text/plain", date="2021-08-30", title="Confidential peer review of urban vacant-lot bee manuscript",
            summary="Achterberg's confidential reviewer report on another group's unpublished manuscript about cavity-nesting bees in urban vacant lots, recommending major revision.",
            keywords=["peer review", "confidential", "service"], sens=("confidential_peer_review",), difficulty="ambiguous")

    # Teaching: syllabus (representative, keep), gradebook (FERPA)
    d = docx.Document(); d.add_heading("ENTM 210: Insects and People - Syllabus, Fall 2019", 0)
    d.add_paragraph("Weeks 1-3 insect diversity; 4-6 pollination and food security (field trip to Hollis Creek Prairie bee plots); "
                    "7-9 disease vectors; 10-14 conservation. Grading: 3 exams 60%, field journal 25%, participation 15%.")
    rel = "Documents/Teaching/ENTM210/ENTM210_Syllabus_F2019.docx"; d.save(reg.p(rel))
    reg.add(rel, "moderate", "One representative syllabus per course is kept", lane="document", fmt="docx", date="2019-08-20",
            title="ENTM 210 Insects and People syllabus, Fall 2019",
            summary="Course syllabus for an introductory insects course with a pollination unit including a field trip to the survey's bee plots.",
            keywords=["syllabus", "teaching", "course"], difficulty="subtle")
    with tempfile.TemporaryDirectory() as td:
        out = soffice(reg.p(rel), "rtf", Path(td))
        shutil.copy(out, reg.p("Documents/Teaching/ENTM210/old/ENTM210_Syllabus_F2017.rtf"))
    reg.add("Documents/Teaching/ENTM210/old/ENTM210_Syllabus_F2017.rtf", "low",
            "Beyond one representative syllabus per course (routine course administration)", lane="document", fmt="rtf",
            date="2017-08-20", title="ENTM 210 syllabus (older copy, RTF)",
            summary="Rich Text copy of the ENTM 210 syllabus; content effectively identical to the 2019 version.",
            keywords=["syllabus", "RTF"], tags=["near_duplicate_text"], difficulty="subtle")
    r = rng("grades")
    wb = Workbook(); ws = wb.active; ws.title = "F2019"
    ws.append(["UIN", "Last", "First", "Exam1", "Exam2", "Exam3", "Journal", "Final %", "Letter"])
    first = ["Ava", "Liam", "Noah", "Emma", "Mia", "Ethan", "Zoe", "Lucas", "Aria", "Owen"]
    last = ["Kowalczyk", "Brennan", "Oduya", "Fairbanks", "Lindgren", "Haddad", "Moreno", "Tsai", "Varga", "Pike"]
    for i in range(48):
        e = [r.randint(55, 99) for _ in range(4)]
        tot = round(sum(e) / 4, 1)
        ws.append([f"6{r.randint(10000000, 99999999)}", r.choice(last), r.choice(first), *e, tot,
                   "A" if tot >= 90 else "B" if tot >= 80 else "C" if tot >= 70 else "D"])
    rel = "Documents/Teaching/ENTM210/grades/ENTM210_F2019_gradebook.xlsx"; wb.save(reg.p(rel))
    reg.add(rel, "none", "Routine course administration (gradebooks); FERPA-protected student records", lane="tabular",
            fmt="xlsx", date="2019-12-18", title="ENTM 210 Fall 2019 gradebook",
            summary="Gradebook of 48 synthetic students with identification numbers, exam and journal scores and letter grades.",
            keywords=["gradebook", "student records", "grades"], sens=("ferpa_student",))
    reg.folder("Documents/Teaching", "low", "Course materials: one syllabus worth keeping, an older duplicate syllabus, and a FERPA-protected gradebook.")

    # HR: PIP letter (restricted)
    d = docx.Document(); d.add_heading("Performance Improvement Plan - CONFIDENTIAL", 0)
    d.add_paragraph("Employee: Doug Penner, Research Technician II. Supervisor: M. Achterberg. Date: June 14, 2019.")
    d.add_paragraph("Concerns: four unexcused absences from scheduled field days (March-May 2019); failure to respond to "
                    "the -80C freezer alarm on May 30-June 1, resulting in loss of approximately 300 DNA extracts.")
    d.add_paragraph("Expectations: notify supervisor before any absence; carry the alarm pager on assigned weekends; "
                    "weekly check-in meetings for 90 days. Employee reports a family medical situation; referred to "
                    "the Employee Assistance Program and FMLA coordinator.")
    rel = "Documents/Admin/Personnel/Penner_PIP_2019-06-14.docx"; d.save(reg.p(rel))
    reg.add(rel, "low", "Personnel matters concerning lab staff must be restricted", lane="document", fmt="docx",
            date="2019-06-14", title="Confidential performance improvement plan for lab technician",
            summary="Performance improvement plan for a research technician citing absences and a freezer failure that destroyed DNA extracts, with expectations and an FMLA referral.",
            keywords=["personnel", "performance improvement plan", "HR"], sens=("hr_personnel", "medical"), difficulty="subtle")

    # Travel reimbursement with SSN (scanned form image -> PDF)
    im = PILImage.new("RGB", (1275, 1650), "white"); dr = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    dr.text((80, 70), "TRAVEL EXPENSE REIMBURSEMENT (SYNTHETIC FORM)", font=fb, fill="black")
    rows = [("Name", "Miriam K. Achterberg"), ("SSN (last required for non-payroll)", "900-41-7733"),
            ("Department", "Entomology"), ("Trip", "Entomological Society Annual Meeting, St. Louis"),
            ("Dates", "Nov 17-20, 2019"), ("Mileage", "334 mi x $0.58 = $193.72"),
            ("Lodging", "$462.00"), ("Meals", "$118.50"), ("TOTAL", "$774.22"),
            ("Direct deposit acct", "Routing 071900001  Acct ****4410")]
    y = 180
    for k, v in rows:
        dr.rectangle([80, y, 1195, y + 70], outline="black")
        dr.text((95, y + 20), k, font=f, fill="black"); dr.text((620, y + 20), v, font=f, fill=(20, 20, 120))
        y += 70
    dr.text((95, y + 60), "Signature: M. Achterberg      Date: 11/25/2019", font=f, fill="black")
    im = im.rotate(0.7, fillcolor="white").filter(ImageFilter.GaussianBlur(0.6))
    rel = "Documents/Admin/Travel/2019_ESA_reimbursement_signed.pdf"
    im.save(reg.p(rel), "PDF", resolution=150)
    reg.add(rel, "none", "Travel booking/reimbursement is routine administration; contains SSN and banking details",
            lane="document", fmt="pdf (image-only scan)", date="2019-11-25",
            title="Signed travel reimbursement form with SSN",
            summary="Scanned travel reimbursement form for the 2019 entomology meeting listing mileage, lodging and meals totals, a Social Security number and partial bank account details.",
            keywords=["reimbursement", "travel", "SSN"], sens=("pii_ssn", "financial_personal"),
            tags=["scanned_image_pdf", "needs_ocr"])

    # Personal: tax return (encrypted PDF), recipes, kid newsletter, fantasy football, household budget
    story = [Paragraph("Form 1040-SYNTHETIC  2021 Individual Income Tax Return", SS["Title"]),
             Paragraph("Filing status: Married filing jointly. Taxpayer: Miriam K. Achterberg SSN 900-41-7733. "
                       "Spouse: Thomas Achterberg SSN 900-52-1186. Dependents: 1.", SS["BodyText"]),
             Paragraph("Wages: $148,220. Interest: $412. Total tax: $21,904. Refund: $1,108.", SS["BodyText"])]
    rel = "Documents/Personal/Taxes/2021_tax_return.pdf"
    pdf_doc(rel, story, "2021 tax return", encrypt=pdfencrypt.StandardEncryption("synthetic-pass", canPrint=0))
    reg.add(rel, "none", "Personal financial and tax records unrelated to university work", lane="document",
            fmt="pdf (password-encrypted)", date="2022-04-10", title="2021 personal income tax return (encrypted)",
            summary="Password-protected PDF of a personal 2021 joint tax return containing Social Security numbers and income figures.",
            keywords=["tax return", "personal finance", "encrypted"], sens=("pii_ssn", "financial_personal"),
            action="route_human_encrypted", tags=["encrypted", "password_protected"])
    reg.p("Documents/Personal/Recipes/grandmas_rhubarb_pie.txt").write_text(
        "Grandma Achterberg's rhubarb pie\n\n4 cups rhubarb, chopped\n1 1/3 cups sugar\n1/3 cup flour\n"
        "pastry for 2-crust pie\n2 Tbsp butter\n\nMix, fill, dot with butter. 425F for 40-50 min.\n"
        "(Use the stalks from the patch by the garage, not the store ones.)\n")
    reg.add("Documents/Personal/Recipes/grandmas_rhubarb_pie.txt", "none", "Household records unrelated to university work",
            lane="document", fmt="text/plain", title="Family rhubarb pie recipe",
            summary="Handed-down family recipe for rhubarb pie.", keywords=["recipe", "personal"])
    wb = Workbook(); ws = wb.active; ws.title = "Week 9"
    ws.append(["Team", "Owner", "W", "L", "PF"])
    for t in [("Bee Keepers", "Tom", 6, 3, 1022), ("Dept Head Hunters", "Adaeze", 5, 4, 988), ("Pollinators", "Miriam", 7, 2, 1101)]:
        ws.append(list(t))
    wb.save(reg.p("Documents/Personal/fantasy_football_2021.xlsx"))
    reg.add("Documents/Personal/fantasy_football_2021.xlsx", "none", "Personal records unrelated to university work",
            lane="tabular", fmt="xlsx", title="Fantasy football league standings 2021",
            summary="Personal fantasy football standings with team names punning on bees.",
            keywords=["fantasy football", "personal"], difficulty="subtle")
    reg.p("Documents/Personal/household_budget_2021.png").write_bytes(charts.unrelated_chart())
    reg.add("Documents/Personal/household_budget_2021.png", "none", "Personal financial records", lane="image",
            fmt="png (chart)", title="Household monthly budget chart 2021",
            summary="Bar chart of monthly household spending categories (mortgage, groceries, utilities).",
            keywords=["household budget", "chart", "personal finance"], sens=("financial_personal",), difficulty="subtle")
    reg.folder("Documents/Personal", "none", "Personal and household material: taxes, recipes, fantasy football, household budget.")
    reg.folder("Documents/Admin", "low", "Administrative records: restricted personnel file and a reimbursement form containing an SSN.")


# ------------------------------------------------------------------ legacy & text oddities
def build_legacy_and_text():
    OLD = "Old_Computer_Backup_2009/My Documents"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        d = docx.Document(); d.add_heading("Wild bee pilot - methods notes (2008)", 1)
        d.add_paragraph("Tried yellow and blue bowls at Hollis Creek, 2 rounds. Blue catches more Melissodes. "
                        "Need a remnant reference - ask county about the Ford Co. farm with the old prairie?")
        d.save(tdp / "pilot_methods_2008.docx")
        out = soffice(tdp / "pilot_methods_2008.docx", "doc", tdp)
        shutil.copy(out, reg.p(f"{OLD}/bees/pilot_methods_2008.doc"))
        reg.add(f"{OLD}/bees/pilot_methods_2008.doc", "high", "Records of the lab's history; earliest methods notes",
                lane="document", fmt="doc (legacy OLE2 Word 97-2003)", date="2008-08-02",
                title="2008 wild bee pilot methods notes",
                summary="Legacy Word note from 2008 comparing yellow and blue pan bowls at Hollis Creek and first proposing a remnant reference site in Ford County.",
                keywords=["pilot", "pan trap", "legacy format", "lab history"], tags=["legacy_format"])
        # mangled extension, same content (POC2 saw .doc1/.career2)
        shutil.copy(out, reg.p(f"{OLD}/bees/pilot_methods_2008 copy.doc1"))
        reg.add(f"{OLD}/bees/pilot_methods_2008 copy.doc1", "high", "Same 2008 methods note under a mangled extension",
                lane="document", fmt="doc (legacy OLE2) with mangled extension", date="2008-08-02",
                title="2008 pilot methods notes (copy with mangled extension)",
                summary="Byte-identical copy of the 2008 pilot methods note saved with a nonstandard '.doc1' extension.",
                keywords=["mangled extension", "duplicate"], action="exclude_duplicate",
                duplicate_of=f"Achterberg_Desktop/{OLD}/bees/pilot_methods_2008.doc",
                tags=["mangled_extension", "duplicate_exact"], difficulty="subtle")
        # extensionless OLE file (Hanratty tree had 38 of these)
        shutil.copy(out, reg.p(f"{OLD}/bees/METHODS"))
        reg.add(f"{OLD}/bees/METHODS", "high", "Same 2008 methods note with no extension",
                lane="document", fmt="doc (legacy OLE2), no extension", date="2008-08-02",
                title="2008 pilot methods notes (extensionless copy)",
                summary="Extensionless byte-identical copy of the 2008 pilot methods note; must be identified by signature, not name.",
                keywords=["no extension", "OLE2", "duplicate"], action="exclude_duplicate",
                duplicate_of=f"Achterberg_Desktop/{OLD}/bees/pilot_methods_2008.doc",
                tags=["no_extension", "duplicate_exact"], difficulty="subtle")
        # legacy xls
        wb = Workbook(); ws = wb.active
        ws.append(["date", "site", "bowl", "count"])
        r = rng("xls2008")
        for day in (5, 19):
            for bowl in ("yellow", "blue"):
                ws.append([f"2008-07-{day:02d}", "HCP", bowl, r.randint(4, 30)])
        wb.save(tdp / "pilot_counts_2008.xlsx")
        out = soffice(tdp / "pilot_counts_2008.xlsx", "xls", tdp)
        shutil.copy(out, reg.p(f"{OLD}/bees/pilot_counts_2008.xls"))
        reg.add(f"{OLD}/bees/pilot_counts_2008.xls", "high", "Original research data (2008 pilot)", lane="tabular",
                fmt="xls (legacy BIFF8)", date="2008-07-19", title="2008 pilot pan-trap counts at Hollis Creek",
                summary="Legacy Excel sheet of 2008 pilot pan-trap counts by date and bowl colour at Hollis Creek Prairie.",
                keywords=["pilot data", "pan trap", "legacy format"], tags=["legacy_format"])
        # ODT
        d = docx.Document(); d.add_paragraph("Letter of support draft for county prairie acquisition (2005).")
        d.add_paragraph("The proposed acquisition adjoins Hollis Creek and would connect two remnant hill prairies.")
        d.save(tdp / "support_letter_2005.docx")
        out = soffice(tdp / "support_letter_2005.docx", "odt", tdp)
        shutil.copy(out, reg.p(f"{OLD}/letters/support_letter_county_prairie_2005.odt"))
        reg.add(f"{OLD}/letters/support_letter_county_prairie_2005.odt", "moderate",
                "Correspondence discussing conservation decisions (pre-survey)", lane="document", fmt="odt",
                date="2005-11-03", title="Draft support letter for county prairie acquisition",
                summary="OpenDocument draft of a 2005 letter supporting a county land acquisition adjoining Hollis Creek.",
                keywords=["letter of support", "land acquisition", "conservation"], difficulty="ambiguous")

    # Windows-1252 encoded text with smart quotes
    t = ("Notes from Prairie Conference \x93Restoring the Grand Prairie\x94 \x96 Aug 2006\r\n"
         "\x95 Packard talk: \x91seed it and they will come\x92? not for bees\r\n"
         "\x95 Idea: compare old vs new restorations \x96 chronosequence!\r\n"
         "\x95 Caf\xe9 at the venue: excellent\r\n").encode("latin-1")
    reg.p(f"{OLD}/notes/prairie_conf_2006.txt").write_bytes(t)
    reg.add(f"{OLD}/notes/prairie_conf_2006.txt", "moderate", "Records documenting the lab's history; origin of the chronosequence idea",
            lane="document", fmt="text/plain; charset=windows-1252, CRLF", date="2006-08-10",
            title="2006 prairie conference notes (origin of chronosequence idea)",
            summary="Windows-1252 encoded conference notes in which Achterberg first jots the idea of comparing old and new restorations as a chronosequence.",
            keywords=["conference notes", "chronosequence", "origin"], tags=["non_utf8_encoding", "crlf"], difficulty="ambiguous")
    # UTF-16 text
    reg.p(f"{OLD}/notes/specimen_loans.txt").write_bytes(
        "Specimen loans out (2009)\nTo: Illinois Natural History Survey - 14 Andrena vouchers\nTo: Bonn - 6 Calliopsis\n".encode("utf-16"))
    reg.add(f"{OLD}/notes/specimen_loans.txt", "moderate", "Specimen records (loan log)", lane="document",
            fmt="text/plain; charset=utf-16 with BOM", date="2009-05-01", title="2009 specimen loan log",
            summary="UTF-16 text listing bee voucher specimens loaned to two institutions in 2009.",
            keywords=["specimen loans", "vouchers"], tags=["non_utf8_encoding"], difficulty="subtle")
    # Saved web page (HTML) and MHTML
    html = ("<html><head><title>Rusty Patched Bumble Bee - Species Profile (SYNTHETIC)</title></head><body>"
            "<h1>Rusty Patched Bumble Bee (Bombus affinis)</h1><p>Status: Endangered (listed 2017). "
            "Once common across the upper Midwest, it has declined by roughly 90%.</p>"
            "<script>var tracking=1;</script><nav>Home | Species | Contact</nav></body></html>")
    reg.p("Downloads/Rusty Patched Bumble Bee - Species Profile.html").write_text(html)
    reg.add("Downloads/Rusty Patched Bumble Bee - Species Profile.html", "low",
            "Downloaded public web page by others, available elsewhere", lane="document", fmt="text/html",
            title="Saved web page: rusty patched bumble bee species profile",
            summary="Saved public species profile web page describing the rusty patched bumble bee's endangered status and decline.",
            keywords=["species profile", "web page", "Bombus affinis"], difficulty="ambiguous")
    mhtml = ("From: <Saved by Blink>\r\nSubject: Burn schedule - Natural Areas\r\nMIME-Version: 1.0\r\n"
             "Content-Type: multipart/related; boundary=\"----B\"\r\n\r\n------B\r\nContent-Type: text/html\r\n"
             "Content-Location: https://dnr.example.gov/burns\r\n\r\n<html><body><h1>2020 prescribed burn schedule</h1>"
             "<p>Sangamon Bend: spring 2020. Kickapoo Ridge: fall 2020.</p></body></html>\r\n------B--\r\n")
    reg.p("Downloads/DNR burn schedule 2020.mhtml").write_text(mhtml)
    reg.add("Downloads/DNR burn schedule 2020.mhtml", "moderate", "Supports site management context for survey sites",
            lane="document", fmt="multipart/related (MHTML)", date="2020-02-10",
            title="Saved DNR prescribed burn schedule 2020 (MHTML)",
            summary="Web archive of the 2020 state prescribed-burn schedule naming two survey sites.",
            keywords=["prescribed burn", "MHTML", "site management"], tags=["mhtml"], difficulty="ambiguous")

    # Desktop clutter
    reg.p("Desktop/TODO.txt").write_text(
        "TODO (May 2024)\n- send Priya the final barcoding table\n- ask Archives about taking the lab files\n"
        "- clean out -80 freezer before retirement\n- give Harold the 2022 bee list for the farm\n- cancel BugSupply account\n")
    reg.add("Desktop/TODO.txt", "moderate", "Records documenting the lab's history (retirement wrap-up)", lane="document",
            fmt="text/plain", date="2024-05-20", title="Retirement to-do list",
            summary="Short to-do list from May 2024 about handing off barcoding data, transferring lab files to the Archives, the freezer and a species list for the landowner.",
            keywords=["to-do", "retirement", "handoff"], difficulty="ambiguous")
    reg.p("Desktop/README_for_archives.md").write_text(
        "# Note for the Archives\n\nThe important stuff is in Documents/Research/Prairie_Bee_Survey.\n"
        "The lab external drive was copied into Documents/Research/Prairie_Bee_Survey/LabDrive_copy.\n"
        "Personal folder can be ignored. BRF locations must stay private (see Karen's email).\n- MKA\n")
    reg.add("Desktop/README_for_archives.md", "high", "Records documenting the collection; donor's own guide to the transfer",
            lane="document", fmt="text/markdown", date="2024-06-01", title="Donor's note to the Archives about the transfer",
            summary="Donor-written Markdown note pointing archivists to the survey folder, explaining the lab drive copy, and reminding that remnant locations must stay private.",
            keywords=["donor note", "finding aid", "provenance"], difficulty="subtle")


def run():
    build_manuscripts(); build_grants(); build_literature(); build_field_notebook()
    build_slides(); build_admin_personal(); build_legacy_and_text()
    reg.folder("Documents", "high", "Main documents tree: research (survey, manuscripts, grants, literature), talks, CV, teaching, service, admin and personal.")
    reg.folder(R, "high", "All research material for the Prairie Bee Survey and its publications and funding.")
    reg.folder("Old_Computer_Backup_2009", "moderate", "Backup of the 2004-2009 computer: legacy Word/Excel/PowerPoint files, encodings, early pilot data and notes.")
    reg.folder("Downloads", "low", "Browser downloads: saved web pages, installers, archives and miscellany.")
    reg.folder("Desktop", "moderate", "Desktop clutter: CV, to-do list, donor's note to the Archives, screenshots.")
