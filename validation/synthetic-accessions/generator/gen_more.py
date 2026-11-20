"""Balance pass: realistic moderate / low / none material that dominates real desktops,
plus 'near-miss' items whose names or words resemble the research but are not it."""
from __future__ import annotations

import io

import docx
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from common import reg, PEOPLE
from gen_emails import build, d
from gen_media import prairie_scene, save_jpg

SS = getSampleStyleSheet()

# (sender, subject, body, date-tuple, relevance, rationale, title, summary, keywords, sens, difficulty)
EMAILS = [
    ("deptadmin", "Faculty meeting agenda - Sept 9", "Agenda: 1) budget update 2) new hire search 3) building renovation timeline 4) teaching assignments spring.",
     (2019, 9, 5), "none", "Routine departmental announcements she did not write", "Faculty meeting agenda",
     "Departmental faculty meeting agenda covering budget, hiring, renovation and teaching assignments.", ["faculty meeting", "agenda"], (), "obvious"),
    ("deptadmin", "Seminar today: Dr. K. Brandt on mosquito vector competence", "Join us at 3 pm for Dr. Brandt's talk on Aedes vector competence. Cookies provided.",
     (2020, 2, 12), "none", "Routine departmental announcements (another speaker, unrelated topic)", "Seminar announcement for another speaker",
     "Department announcement of a visiting speaker's seminar on mosquito vector competence.", ["seminar", "announcement"], (), "subtle"),
    ("deptadmin", "Reminder: annual ethics training due Dec 31", "All employees must complete the annual ethics training module by December 31.",
     (2021, 11, 15), "none", "Routine administrative notices", "Ethics training reminder", "Annual ethics training compliance reminder.", ["training", "compliance"], (), "obvious"),
    ("it", "Scheduled maintenance: email outage Saturday 2-6 am", "Email services will be unavailable Saturday from 2 to 6 am for maintenance.",
     (2019, 3, 20), "none", "Routine IT messages", "Email maintenance notice", "IT notice of a scheduled email outage.", ["IT", "maintenance"], (), "obvious"),
    ("Illinois Prairie Society <board@prairiesociety.example.org>", "Board minutes + vote on research grants",
     "Minutes attached in body. Moved (Achterberg) and seconded to fund two student research grants on prairie insects at $1,500 each; passed 7-0. "
     "Discussion of the society's position on solar development on former prairie remnants; Achterberg to draft a statement.",
     (2021, 1, 22), "moderate", "Service records related to her research field (prairie society board)", "Prairie society board minutes with her motion",
     "Board minutes of a prairie conservation society recording Achterberg's motion to fund student insect research and her assignment to draft a statement on solar development.",
     ["service", "board minutes", "prairie conservation"], (), "subtle"),
    ("Grad Program Office <ento-grad@illinois.example.edu>", "Prelim exam scheduled: P. Natarajan",
     "Priya Natarajan's preliminary exam is scheduled for April 3 at 10 am. Committee: Achterberg (chair), Quintero, Lindgren, Moss.",
     (2020, 3, 10), "low", "Student records (FERPA) with minor relevance to supervised dissertation", "Preliminary exam scheduling for advisee",
     "Graduate office notice scheduling a PhD student's preliminary exam and listing her committee.", ["graduate student", "exam"], ("ferpa_student",), "subtle"),
    ("Journal of Insect Conservation <jic@journals.example.org>", "Invitation to review JIC-2022-0567",
     "Dear Dr. Achterberg, would you be willing to review 'Mowing regimes and butterfly abundance in roadside verges'? Please respond within 7 days.",
     (2022, 2, 3), "low", "Review invitation (service logistics); no review content", "Peer review invitation",
     "Journal invitation to review a manuscript on roadside mowing and butterflies.", ["review invitation", "service"], (), "subtle"),
    ("Amazon.example <ship-confirm@amazon.example.com>", "Your order has shipped: 6 x Solo 3.25 oz plastic bowls (500 ct)",
     "Your order of 6 cases of 3.25 oz plastic bowls (blue, yellow, white) has shipped to Entomology Receiving. Order total $214.88 (department card).",
     (2019, 4, 18), "low", "Purchase confirmation; incidentally documents survey supplies", "Order confirmation for pan-trap bowls",
     "Shipping confirmation for cases of coloured plastic bowls used as pan traps, paid on a department card.", ["purchase", "supplies", "pan trap"], (), "ambiguous"),
    ("tom", "Re: summer vacation?", "Lake house week of Aug 14 works if you're not in the field. Kids want to bring the dog.",
     (2021, 5, 30), "none", "Personal records", "Spouse message about vacation", "Personal note about a family lake vacation.", ["personal", "vacation"], (), "obvious"),
    ("Champaign Unit 4 Schools <news@unit4.example.org>", "Westview Elementary Newsletter - March",
     "Spring picture day is March 12. Science fair projects due March 20 - this year's theme is 'Pollinators!'",
     (2018, 3, 1), "none", "Personal records; mention of pollinators is incidental", "Elementary school newsletter mentioning pollinators",
     "Child's school newsletter announcing picture day and a pollinator-themed science fair.", ["school newsletter", "personal"], ("minor_child",), "ambiguous"),
    ("quintero", "fantasy draft order", "You pick 3rd this year. Don't take a kicker in round 2 again.",
     (2021, 8, 20), "none", "Personal records (collaborator, but personal topic)", "Collaborator email about fantasy football",
     "Personal message from her statistician collaborator about a fantasy football draft.", ["personal", "fantasy football"], (), "ambiguous"),
    ("natarajan", "Can't make lab meeting - sick", "Hi Miriam, I have a fever and will stay home today. Sorry! Priya",
     (2020, 1, 28), "none", "Routine absence notice; contains health information about a student", "Student absence notice for illness",
     "Student informs advisor she is sick and will miss lab meeting.", ["absence", "illness"], ("medical", "ferpa_student"), "subtle"),
    ("feld", "bowls for Thursday?", "Do we have enough yellow bowls for Thursday or should I pick some up? Jonah",
     (2019, 6, 10), "low", "Routine logistics within the survey; little informational value", "Student question about supply of yellow bowls",
     "One-line logistics question from a student about pan-trap bowl supplies for an upcoming field day.", ["logistics", "pan trap"], (), "ambiguous"),
    ("lindqvist", "Re: burn permits Cardinal Bluff & Lafayette Rd",
     "Miriam, permits for the burn-versus-mow plots are approved for March 15 - April 30, 2021, contingent on a burn boss on site. "
     "Please send plot maps and the smoke management plan by Feb 26.",
     (2021, 2, 11), "high", "Correspondence with DNR staff about methods and site access (experiment permits)", "DNR approves burn permits for experiment",
     "Illinois DNR approves prescribed-burn permits for the burn-versus-mow experiment plots with conditions and a deadline for plot maps.",
     ["burn permit", "experiment", "Illinois DNR"], (), "obvious"),
    ("okonkwo", "Congratulations on your retirement", "Miriam - eighteen years, one hundred students, and a few thousand bees. The department will miss you. Party is June 7 at 4.",
     (2024, 5, 2), "moderate", "Records documenting her career", "Department head's retirement congratulations",
     "Department head congratulates Achterberg on retirement, summarising her career, and announces the party.", ["retirement", "career"], (), "subtle"),
    ("Conference Registration <noreply@esa-meeting.example.org>", "Abstract accepted: Poster P-311",
     "Your abstract 'Bare ground predicts recovery of ground-nesting bees in restored prairie' (Feld J, Achterberg MK) has been accepted as poster P-311.",
     (2020, 8, 25), "moderate", "Record of presenting the research (acceptance notice, not the poster itself)", "Conference poster acceptance",
     "Conference acceptance of a student poster on bare ground and ground-nesting bee recovery.", ["conference", "poster", "abstract"], (), "subtle"),
    ("SurveyMonkey <member@surveymonkey.example.com>", "We want your feedback!", "Tell us how we're doing - take our 2-minute survey!",
     (2020, 6, 1), "none", "Vendor marketing (word 'survey' is a near miss)", "Marketing feedback request",
     "Generic vendor marketing email asking for feedback; the word 'survey' is unrelated to the bee survey.", ["marketing", "near miss"], (), "subtle"),
]


def build_emails():
    for i, (snd, subj, body, dt, rel, why, title, summ, kw, sens, diff) in enumerate(EMAILS):
        m = build(snd, ["achterberg"], subj, body, d(*dt, 9 + i % 8, (i * 7) % 60))
        folder = {"high": "Prairie_Bee_Survey", "moderate": "Professional", "low": "Misc", "none": "Misc"}[rel]
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in subj)[:55].strip()
        path = f"Email/Saved_Messages/{folder}/{30 + i:02d}_{safe}.eml"
        reg.p(path).write_bytes(bytes(m))
        reg.add(path, rel, why, lane="email", title=title, summary=summ, keywords=kw, sens=sens or ("none",),
                difficulty=diff, fmt="message/rfc822", date=m["Date"])


# (rel, kind, text, relevance, rationale, title, summary, keywords, sens, difficulty)
FILES = [
    ("Documents/Service/Prairie_Society/statement_solar_on_remnants_DRAFT.docx", "docx",
     "Draft statement: Solar development should avoid unplowed prairie remnants. Remnants hold soil organisms and specialist insects, including ground-nesting bees, that do not return quickly after disturbance (see Achterberg et al. 2021).",
     "moderate", "Service work that applies her research findings", "Draft society statement on solar development and prairie remnants",
     "Draft position statement for a prairie society arguing solar projects should avoid remnants, citing her specialist-bee findings.", ["service", "policy statement", "remnant prairie"], (), "subtle"),
    ("Documents/Service/Promotion_Committee/2022_dossier_review_notes.docx", "docx",
     "Confidential: notes on Dr. J. Lindgren's promotion dossier. Teaching evaluations strong (4.6/5). Research: 11 papers, 2 as senior author. Concern: external letter 3 is lukewarm.",
     "low", "Personnel matters (promotion review of a colleague) must be restricted", "Confidential promotion-dossier review notes",
     "Achterberg's confidential committee notes evaluating a colleague's promotion dossier.", ["promotion", "personnel", "committee"], ("hr_personnel",), "subtle"),
    ("Documents/Teaching/ENTM210/lectures/week05_pollination.pptx", "pptx",
     "Week 5: Pollination and food security|Why bees matter: ~35% of crop production benefits from animal pollination|Our local example: native bees on restored prairie (Hollis Creek field trip)",
     "moderate", "Teaching materials drawing on her research", "Lecture slides on pollination for intro course",
     "Introductory lecture deck on pollination and food security that uses her prairie bee sites as a local example.", ["lecture", "teaching", "pollination"], (), "subtle"),
    ("Documents/Teaching/ENTM210/lectures/week08_mosquitoes.pptx", "pptx",
     "Week 8: Mosquitoes and disease|Aedes, Culex, Anopheles|West Nile virus in Illinois",
     "low", "Routine teaching material unrelated to her research", "Lecture slides on mosquitoes and disease",
     "Introductory lecture deck on mosquito-borne disease, unrelated to her research.", ["lecture", "mosquitoes"], (), "subtle"),
    ("Documents/Teaching/ENTM210/roster_F2019.csv", "csv",
     "UIN,name,email,major\n612345678,Ava Kowalczyk,akowal2@illinois.example.edu,Biology\n687654321,Liam Brennan,lbren4@illinois.example.edu,Agriculture\n",
     "none", "Routine course administration (rosters); FERPA", "ENTM 210 class roster", "Class roster with student IDs, names, emails and majors.",
     ["roster", "student records"], ("ferpa_student",), "obvious"),
    ("Documents/Lab_Admin/lab_safety_SOP_ethanol.pdf", "pdf",
     "Standard Operating Procedure: Ethanol storage and handling. Store no more than 10 L of 70% ethanol outside the flammables cabinet. Label all specimen vials.",
     "low", "Routine lab administration; tangential to specimen handling", "Lab safety SOP for ethanol",
     "Laboratory standard operating procedure for storing and handling ethanol used for specimens.", ["safety", "SOP", "ethanol"], (), "subtle"),
    ("Documents/Lab_Admin/lab_roster_and_keys_2020.xlsx", "xlsx",
     "name|role|room keys|phone\nPriya Natarajan|PhD student|318, 320|(555) 0123\nJonah Feld|MS student|320|(555) 0156\nDoug Penner|Technician|318, 320, freezer|(555) 0109",
     "low", "Lab administration with contact details; minor value for lab history", "Lab member roster with keys and phones",
     "Spreadsheet listing lab members, roles, room key assignments and phone numbers in 2020.", ["lab roster", "keys", "contacts"], ("pii_contact",), "ambiguous"),
    ("Documents/Research/Other_projects/Brandt_mosquito_collab/aedes_counts_2017.csv", "csv",
     "trap,date,aedes_albopictus,culex_pipiens\nT1,2017-07-01,12,30\nT2,2017-07-01,4,51\n",
     "low", "Research data from a side collaboration outside the scope of the bee survey", "Mosquito trap counts from a 2017 side collaboration",
     "Small CSV of mosquito trap counts from a collaboration with another lab; research data but outside the prairie bee scope.", ["mosquito", "trap counts", "collaboration"], (), "ambiguous"),
    ("Documents/Research/Other_projects/Monarch_citizen_science_2014/notes.txt", "txt",
     "Monarch tagging with the county 4-H club, Sept 2014. 212 tagged at Hollis Creek. Two recoveries reported from Mexico (2015). Fun outreach, no publication planned.",
     "moderate", "Earlier outreach research at a survey site (career record)", "Notes on 2014 monarch tagging outreach at Hollis Creek",
     "Notes on a 2014 citizen-science monarch butterfly tagging event at a future survey site, with two long-distance recoveries.", ["monarch", "outreach", "citizen science"], (), "ambiguous"),
    ("Downloads/Bee_Movie_script.txt", "txt",
     "According to all known laws of aviation, there is no way a bee should be able to fly... [synthetic placeholder for a downloaded film script]",
     "none", "Personal download; bee topic is a near miss", "Downloaded movie script about a bee",
     "Placeholder for a downloaded animated-film script featuring a bee; entertainment, not research.", ["near miss", "entertainment"], (), "subtle"),
    ("Downloads/beekeeping_supplies_catalog_2020.pdf", "pdf",
     "Honey bee hive bodies, frames, smokers, veils. Spring catalog 2020. Free shipping over $99.",
     "none", "Vendor marketing (honey bee keeping, not wild bee research)", "Beekeeping supplies catalog",
     "Vendor catalog for honey bee keeping equipment; managed honey bees are outside her wild-bee research.", ["catalog", "beekeeping", "near miss"], (), "subtle"),
    ("Downloads/Conference_Program_ESA_2019.pdf", "pdf",
     "Entomological Society Annual Meeting 2019 - Program. Session 4B Pollinator Ecology: 10:15 Achterberg MK, 'Ground-nesting bees lag in restored prairie'.",
     "low", "Program for a conference (mostly others); lists her talk", "Annual meeting conference program listing her talk",
     "Large conference program in which one session lists Achterberg's talk on ground-nesting bees.", ["conference program", "talk listing"], (), "ambiguous"),
    ("Downloads/W-4_2020_blank.pdf", "pdf", "Form W-4-SYNTHETIC Employee's Withholding Certificate (blank).",
     "none", "Personal financial forms", "Blank tax withholding form", "Blank employee withholding form download.", ["tax form", "blank form"], (), "obvious"),
    ("Documents/Personal/Medical/PT_exercises_knee.docx", "docx", "Physical therapy home exercises after knee surgery: quad sets 3x10, heel slides 3x10, ice 20 min.",
     "none", "Personal medical records", "Physical therapy exercise sheet", "Personal post-surgery physical therapy instructions.", ["medical", "personal"], ("medical",), "obvious"),
    ("Documents/Personal/Car/insurance_card_2022.pdf", "pdf", "Auto insurance ID card (SYNTHETIC). Policy 77-1182-993. Vehicle 2016 Subaru Outback. Insured: Thomas & Miriam Achterberg.",
     "none", "Personal and household records", "Auto insurance card", "Personal vehicle insurance identification card.", ["insurance", "personal"], ("financial_personal",), "obvious"),
    ("Documents/Personal/garden_plan_2020.xlsx", "xlsx",
     "bed|plants|notes\nfront|Monarda, Echinacea, Zizia|for the bees!\nback|tomatoes, basil|\nside|rhubarb|grandma's",
     "none", "Household records unrelated to university work (bee-friendly garden is a near miss)", "Home garden planting plan",
     "Personal home garden plan noting bee-friendly native plants in one bed.", ["garden", "personal", "near miss"], (), "ambiguous"),
    ("Desktop/wifi_password.txt", "txt", "Home wifi: AchterbergHome / SYNTHETIC-not-a-real-password-42\nOffice printer PIN: 0000\n",
     "none", "Credentials must be flagged and never published", "Plain-text home wifi password", "Text file holding a home wifi network name and password and a printer PIN.",
     ["password", "credentials"], ("credentials",), "obvious"),
]


def build_files():
    for rel, kind, text, relevance, why, title, summ, kw, sens, diff in FILES:
        p = reg.p(rel)
        fmt = kind
        if kind == "docx":
            dd = docx.Document()
            for para in text.split("|"):
                dd.add_paragraph(para)
            dd.save(p)
        elif kind == "pptx":
            from pptx import Presentation
            prs = Presentation(); parts = text.split("|")
            s = prs.slides.add_slide(prs.slide_layouts[0]); s.shapes.title.text = parts[0]; s.placeholders[1].text = "ENTM 210"
            for t in parts[1:]:
                sl = prs.slides.add_slide(prs.slide_layouts[1]); sl.shapes.title.text = t.split(":")[0]; sl.placeholders[1].text = t
            prs.save(p)
        elif kind == "xlsx":
            wb = Workbook(); ws = wb.active
            for line in text.split("\n"):
                ws.append(line.split("|"))
            wb.save(p)
        elif kind == "pdf":
            SimpleDocTemplate(str(p), pagesize=letter).build([Paragraph(x, SS["BodyText"]) for x in text.split("|")])
        else:
            p.write_text(text)
            fmt = "text/csv" if kind == "csv" else "text/plain"
        lane = {"csv": "tabular", "xlsx": "tabular"}.get(kind, "document")
        reg.add(rel, relevance, why, lane=lane, fmt=fmt, title=title, summary=summ, keywords=kw,
                sens=sens or ("none",), difficulty=diff)

    # Near-miss and irrelevant photos
    for k, (rel, rel_, why, title, summ, dt, gps, stage) in enumerate([
        ("Pictures/Phone/IMG_20190921_134402.jpg", "none", "Personal photograph (prairie scenery on vacation, not a survey site)",
         "Vacation photo of grassland in another state", "Personal phone photo of grassland scenery on a family trip to Kansas; resembles a survey photo but is not one.",
         "2019:09:21 13:44:02", (38.47, -96.55), "mature"),
        ("Pictures/Phone/IMG_20220514_101500.jpg", "moderate", "Possibly a field photograph of a survey site, taken on a personal phone",
         "Phone photo of a prairie planting at a survey site", "Phone photo of a young prairie planting whose GPS matches the Lafayette Road survey site; no notes or caption.",
         "2022:05:14 10:15:00", (40.0602, -88.2412), "young"),
    ]):
        im = prairie_scene(900 + k, w=1400, h=1050, stage=stage)
        save_jpg(im, rel, dt, gps=gps, make="Google", model="Pixel 3a")
        reg.add(rel, rel_, why, lane="image", fmt="jpeg (phone, GPS)", date=dt[:10].replace(":", "-"), title=title, summary=summ,
                keywords=["phone photo", "prairie", "GPS"], tags=["exif_gps"], difficulty="ambiguous")

    reg.folder("Documents/Service", "moderate", "Service: prairie society statement, confidential promotion notes, a confidential peer review.")
    reg.folder("Documents/Research/Other_projects", "low", "Side projects outside the bee survey: mosquito collaboration data and 2014 monarch outreach notes.")
    reg.folder("Documents/Lab_Admin", "low", "Lab administration: safety SOP, roster with keys and phones, lab logo files.")


def run():
    build_emails(); build_files()
