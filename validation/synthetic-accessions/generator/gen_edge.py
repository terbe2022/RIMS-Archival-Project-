"""Edge cases: system files, duplicates, corruption, misleading names, containers."""
from __future__ import annotations

import gzip
import io
import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

from common import reg, rng, ROOT, ROOT_NAME

PBS = "Documents/Research/Prairie_Bee_Survey"


def sysfile(rel, data, fmt, title):
    reg.p(rel).write_bytes(data)
    reg.add(rel, "none", "Operating-system files and application caches", lane="system", fmt=fmt,
            action="exclude_system_file", title=title, summary=f"{title}; no content of archival value.",
            keywords=["system file"], tags=["system_file"])


def build_system():
    sysfile("Desktop/.DS_Store", b"\x00\x00\x00\x01Bud1" + bytes(rng("ds").randrange(256) for _ in range(6140)), "macOS .DS_Store", "macOS Finder metadata file")
    sysfile(f"{PBS}/field_photos/2019/SBP/.DS_Store", b"\x00\x00\x00\x01Bud1" + b"\x00" * 2044, "macOS .DS_Store", "macOS Finder metadata file")
    sysfile("Old_Computer_Backup_2009/My Documents/My Pictures/Thumbs.db",
            bytes.fromhex("D0CF11E0A1B11AE1") + b"\x00" * 4088, "Windows thumbnail cache (OLE2)", "Windows thumbnail cache")
    sysfile("Old_Computer_Backup_2009/My Documents/desktop.ini",
            "[.ShellClassInfo]\r\nLocalizedResourceName=@%SystemRoot%\\system32\\shell32.dll,-21770\r\n".encode("utf-16"),
            "Windows desktop.ini", "Windows folder settings file")
    sysfile("Desktop/.localized", b"", "macOS .localized (zero bytes)", "macOS folder localization marker")
    sysfile("Downloads/.~lock.budget.xlsx#", b"Miriam Achterberg,machterberg,OFFICE-PC,13.11.2023 10:02,file:///C:/Users/machterberg/AppData/Roaming/LibreOffice/4;",
            "LibreOffice lock file", "LibreOffice lock file")
    reg.p("Documents/Research/Prairie_Bee_Survey/analysis/.Rhistory").write_text(
        "library(mgcv)\nd <- read.csv('../data/processed/richness_by_site_year.csv')\nm_all <- gam(richness ~ s(age_c,k=5), data=d)\nplot(m_all)\nq()\n")
    reg.add("Documents/Research/Prairie_Bee_Survey/analysis/.Rhistory", "low", "Application history file; fragments of analysis commands",
            lane="code", fmt="R history", title="R console history", summary="Hidden R history file with a few commands fitting and plotting the richness model.",
            keywords=["R history", "hidden file"], tags=["hidden_file"], difficulty="ambiguous")


def build_broken_and_misleading():
    # zero-byte file with a promising name
    reg.p(f"{PBS}/data/raw/pantrap_specimens_2023.csv").write_bytes(b"")
    reg.add(f"{PBS}/data/raw/pantrap_specimens_2023.csv", "none", "Empty file: no content despite a relevant name",
            lane="tabular", fmt="empty (0 bytes)", title="Empty 2023 pan-trap file",
            summary="Zero-byte file named like a 2023 data file; the 2023 season was never collected. Name alone must not drive relevance.",
            keywords=["empty file", "zero bytes"], action="route_human_corrupt", tags=["zero_byte", "misleading_name"], difficulty="subtle")
    # truncated PDF (corrupt)
    src = (ROOT / "Documents/Research/Manuscripts/2021_JPE_restoration_age/published/Achterberg_etal_2021_JPE.pdf").read_bytes()
    reg.p("Downloads/Achterberg_etal_2021_JPE (1).pdf").write_bytes(src[: len(src) // 3])
    reg.add("Downloads/Achterberg_etal_2021_JPE (1).pdf", "high", "Published results (but file is a truncated/incomplete download)",
            lane="document", fmt="pdf (truncated, no xref/trailer)", title="Truncated download of the 2021 published article",
            summary="Incomplete browser download of the 2021 article: first third of the PDF bytes, missing cross-reference table; text may partly extract. A complete copy exists in Manuscripts/published.",
            keywords=["corrupt", "truncated PDF", "partial download"], action="route_human_corrupt", tags=["corrupt", "truncated"], difficulty="subtle")
    # corrupt JPEG (header ok, body garbage)
    good = (ROOT / f"{PBS}/field_photos/2019/SBP").glob("*.JPG")
    data = next(good).read_bytes()
    r = rng("corrupt")
    bad = bytearray(data);
    for i in range(2000, len(bad), 97):
        bad[i] = r.randrange(256)
    reg.p(f"{PBS}/field_photos/2019/SBP/IMG_4000_damaged.JPG").write_bytes(bytes(bad[: len(bad) * 2 // 3]))
    reg.add(f"{PBS}/field_photos/2019/SBP/IMG_4000_damaged.JPG", "moderate", "Field photograph, but damaged/partially unreadable",
            lane="image", fmt="jpeg (corrupted scan data, truncated)", date="2019-06-16",
            title="Damaged copy of a Sangamon Bend field photograph",
            summary="JPEG with valid header and EXIF but corrupted, truncated image data; should be flagged as damaged rather than described.",
            keywords=["corrupt image", "damaged"], action="route_human_corrupt", tags=["corrupt"], difficulty="subtle")
    # misleading extensions
    shutil.copy(ROOT / "Documents/Research/Grants/NSF_DEB-1900417/reports/Annual_Report_Y2_2021.docx", reg.p("Desktop/notes.txt"))
    reg.add("Desktop/notes.txt", "high", "Progress report for NSF award (DOCX bytes saved with .txt extension)", lane="document",
            fmt="docx (OOXML zip) misnamed .txt", date="2021-08-30", title="NSF year-2 report hidden under a .txt name",
            summary="A Word document (ZIP/OOXML signature) misnamed notes.txt; byte-identical to the year-2 NSF annual report. Must be identified by signature.",
            keywords=["misleading extension", "NSF report"], action="exclude_duplicate",
            duplicate_of=f"{ROOT_NAME}/Documents/Research/Grants/NSF_DEB-1900417/reports/Annual_Report_Y2_2021.docx",
            tags=["misleading_extension", "duplicate_exact"], difficulty="subtle")
    shutil.copy(ROOT / f"{PBS}/figures/fig2_specialists_age.png", reg.p("Downloads/image(3).jpg"))
    reg.add("Downloads/image(3).jpg", "high", "Figure generated by the analysis (PNG bytes with .jpg extension)", lane="image",
            fmt="png misnamed .jpg", title="Specialist richness figure saved as .jpg",
            summary="PNG chart of specialist richness vs restoration age saved with a .jpg extension; exact duplicate of Figure 2.",
            keywords=["misleading extension", "figure"], action="exclude_duplicate",
            duplicate_of=f"{ROOT_NAME}/{PBS}/figures/fig2_specialists_age.png", tags=["misleading_extension", "duplicate_exact"], difficulty="subtle")
    # unidentifiable binary blobs
    r = rng("blob")
    reg.p(f"{PBS}/LabDrive_copy/instrument/net3852448d").write_bytes(b"\x89SPX" + bytes(r.randrange(256) for _ in range(30000)))
    reg.add(f"{PBS}/LabDrive_copy/instrument/net3852448d", "moderate", "Unidentifiable instrument file in a research folder; relevance only from folder context",
            lane="unknown", fmt="unidentified binary", title="Unidentified binary instrument file",
            summary="Proprietary-looking binary with no recognised signature or extension in the lab drive's instrument folder; should go to the human queue with folder context.",
            keywords=["unidentified format", "instrument"], action="route_human_unidentified", tags=["no_extension", "unidentified"], difficulty="ambiguous")
    reg.p(f"{PBS}/LabDrive_copy/instrument/spectro_run12.career2").write_bytes(b"SPECTRO-V2\x00" + bytes(r.randrange(256) for _ in range(12000)))
    reg.add(f"{PBS}/LabDrive_copy/instrument/spectro_run12.career2", "moderate", "Unidentifiable proprietary instrument output in research folder",
            lane="unknown", fmt="unidentified binary with nonsense extension", title="Proprietary spectrometer output (unknown format)",
            summary="Binary file with a meaningless '.career2' extension and an ASCII 'SPECTRO-V2' header; format unidentified.",
            keywords=["unidentified format", "mangled extension"], action="route_human_unidentified", tags=["mangled_extension", "unidentified"], difficulty="ambiguous")
    # Installer & executables (excluded)
    reg.p("Downloads/R-4.0.2.pkg").write_bytes(b"xar!\x00\x1c\x00\x01" + bytes(r.randrange(256) for _ in range(400000)))
    reg.add("Downloads/R-4.0.2.pkg", "none", "Installers and software downloads", lane="system", fmt="macOS installer package (xar)",
            title="R 4.0.2 installer package", summary="macOS installer package for R (synthetic bytes with xar signature).",
            keywords=["installer", "software"], action="exclude_system_file", tags=["installer"])
    reg.p("Downloads/ZoomInstaller.exe").write_bytes(b"MZ\x90\x00\x03" + b"\x00" * 59 + b"PE\x00\x00" + bytes(r.randrange(256) for _ in range(200000)))
    reg.add("Downloads/ZoomInstaller.exe", "none", "Installers and software downloads", lane="system", fmt="Windows PE executable",
            title="Zoom installer executable", summary="Windows executable installer (synthetic bytes with MZ/PE header).",
            keywords=["installer", "executable"], action="exclude_system_file", tags=["installer", "executable"])
    # Shortcuts, contacts, calendar
    reg.p("Desktop/Prairie Bee Survey - Shortcut.lnk").write_bytes(bytes.fromhex("4C0000000114020000000000C000000000000046") + b"\x00" * 60 +
                                                                 "C:\\Users\\machterberg\\Documents\\Research\\Prairie_Bee_Survey".encode("utf-16-le"))
    reg.add("Desktop/Prairie Bee Survey - Shortcut.lnk", "none", "Operating-system shortcut; points to a folder already in the transfer",
            lane="system", fmt="Windows shell link (.lnk)", title="Desktop shortcut to the survey folder",
            summary="Windows shortcut pointing to the Prairie Bee Survey folder; no content of its own.",
            keywords=["shortcut"], action="exclude_system_file", tags=["system_file", "shortcut"], difficulty="subtle")
    reg.p("Desktop/BOLD Systems.url").write_text("[InternetShortcut]\r\nURL=https://www.boldsystems.example.org/\r\n")
    reg.add("Desktop/BOLD Systems.url", "none", "Browser bookmark file", lane="system", fmt="Internet shortcut", title="Bookmark to barcode database",
            summary="Internet shortcut to a DNA barcode database website.", keywords=["bookmark"], action="exclude_system_file", tags=["shortcut"], difficulty="subtle")
    vcf = "".join(f"BEGIN:VCARD\r\nVERSION:3.0\r\nFN:{n}\r\nEMAIL:{e}\r\nTEL:{t}\r\nORG:{o}\r\nEND:VCARD\r\n" for n, e, t, o in [
        ("Harold Ritter", "hjritter.farm@mailbox.example.com", "(555) 0142", "Ritter Farm"),
        ("Karen Lindqvist", "karen.lindqvist@dnr.illinois.example.gov", "(555) 0177", "Illinois DNR"),
        ("Rafael Quintero", "rquintero@stats.prairiestate.example.edu", "(555) 0110", "Prairie State University")])
    reg.p("Documents/Contacts/field_contacts.vcf").write_text(vcf)
    reg.add("Documents/Contacts/field_contacts.vcf", "moderate", "Contacts of collaborators, DNR staff and landowners (supports correspondence context)",
            lane="document", fmt="vCard 3.0", title="Contact cards for landowner, DNR and collaborator",
            summary="Three vCards with names, emails and phone numbers for the remnant landowner, the DNR contact and the statistician.",
            keywords=["contacts", "vCard"], sens=("pii_contact",), difficulty="ambiguous")
    reg.p("Documents/Calendar/field_season_2020.ics").write_text(
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Synthetic//EN\r\n" + "".join(
            f"BEGIN:VEVENT\r\nUID:pbs2020-{i}\r\nDTSTART;VALUE=DATE:2020{m:02d}{d:02d}\r\nSUMMARY:PBS round {i + 1} - all sites\r\nEND:VEVENT\r\n"
            for i, (m, d) in enumerate([(5, 20), (6, 14), (7, 12), (8, 9)])) + "END:VCALENDAR\r\n")
    reg.add("Documents/Calendar/field_season_2020.ics", "moderate", "Records of field season scheduling", lane="document", fmt="iCalendar",
            date="2020-05-01", title="2020 field season calendar", summary="iCalendar with the four 2020 sampling rounds.",
            keywords=["calendar", "field season", "schedule"], difficulty="subtle")


def build_names_and_nesting():
    # unicode + long filename + deep nesting
    reg.p("Documents/Research/Collaborations/Bonn_2009/Ergebnisse_Wildbienen_Übersicht_–_Änderungen.txt").write_text(
        "Übersicht der Wildbienen-Bestimmungen (Bonn, Juli 2009)\nAndrena: 14 Exemplare überprüft, 2 Fehlbestimmungen korrigiert.\n", encoding="utf-8")
    reg.add("Documents/Research/Collaborations/Bonn_2009/Ergebnisse_Wildbienen_Übersicht_–_Änderungen.txt", "moderate",
            "Correspondence/records of collaboration on specimen identification", lane="document", fmt="text/plain (UTF-8, German)",
            date="2009-07-20", title="German summary of bee identification checks in Bonn",
            summary="German-language note recording that 14 Andrena specimens were rechecked in Bonn in 2009 and two misidentifications corrected; non-ASCII filename.",
            keywords=["identification", "German", "collaboration"], tags=["unicode_filename", "non_english"], difficulty="subtle")
    long_name = ("FINAL_FINAL_revised_after_meeting_with_Rafael_and_Priya_use_this_one_NOT_the_other_one_"
                 "specialist_lag_discussion_paragraph_for_JPE_revision_november_2020_v7b.txt")
    reg.p(f"Desktop/{long_name}").write_text(T_DISC := (
        "Discussion paragraph (revision): The remnant anchors the specialist gradient. We therefore present it as a reference "
        "condition rather than a sample point, and show the specialist trend without it in Fig. S4 (p = 0.03).\n"))
    reg.add(f"Desktop/{long_name}", "high", "Drafts of manuscripts showing how the paper changed", lane="document", fmt="text/plain",
            date="2020-11-18", title="Revised discussion paragraph on specialist lag",
            summary="Draft revision paragraph framing the remnant as a reference condition and citing the Fig. S4 sensitivity analysis.",
            keywords=["manuscript revision", "discussion"], tags=["long_filename"], difficulty="subtle")
    deep = "Documents/Research/Prairie_Bee_Survey/LabDrive_copy/old/backup/2018/from_laptop/Desktop/New Folder/New Folder (2)/stuff/keep"
    reg.p(f"{deep}/2018_station_coords_handheld.csv").write_text(
        "site,station,lat,lon\nBRF,1,40.55241,-88.01672\nBRF,2,40.55263,-88.01601\nBRF,3,40.55290,-88.01540\nSBP,1,40.07131,-88.64322\n")
    reg.add(f"{deep}/2018_station_coords_handheld.csv", "high", "Original research data: site metadata (station coordinates)", lane="tabular",
            fmt="text/csv", date="2018-06-01", title="Handheld GPS coordinates of trap stations, 2018",
            summary="Small CSV of trap-station coordinates including the three stations on the private remnant; buried 14 folders deep.",
            keywords=["coordinates", "trap stations", "GPS"], sens=("sensitive_location",), tags=["deep_nesting"], difficulty="subtle")
    reg.folder(f"{deep}", "high", "Deeply nested 'New Folder' chain ending in a small but important coordinates file.")
    reg.p("Documents/Research/Prairie_Bee_Survey/LabDrive_copy/old/backup/2018/from_laptop/Desktop/New Folder/New Folder (2)/empty_folder_placeholder/.keep").write_bytes(b"")
    reg.add("Documents/Research/Prairie_Bee_Survey/LabDrive_copy/old/backup/2018/from_laptop/Desktop/New Folder/New Folder (2)/empty_folder_placeholder/.keep",
            "none", "Placeholder for an otherwise empty folder (git cannot store empty dirs)", lane="system", fmt="empty (0 bytes)",
            title="Empty-folder placeholder", summary="Zero-byte placeholder keeping an empty folder in the transfer.",
            keywords=["empty folder"], action="exclude_system_file", tags=["zero_byte", "empty_folder"])


def build_duplicates():
    for src, dst in [(f"{PBS}/field_photos/2019/BRF/IMG_4148.JPG", "Downloads/IMG_4148.JPG"),
                     (f"{PBS}/data/raw/pantrap_specimens_2019.csv", "Desktop/pantrap_specimens_2019 (copy).csv"),
                     ("Documents/CV/Achterberg_CV_2024.docx", "Downloads/Achterberg_CV_2024.docx")]:
        shutil.copy(ROOT / src, reg.p(dst))
        o = reg.labels[f"{ROOT_NAME}/{src}"]
        reg.add(dst, o.relevance, "Exact duplicate of a file kept elsewhere in the transfer", lane=o.lane, fmt=o.true_format,
                title=o.gt_title + " (exact duplicate)", summary="Byte-identical copy of " + src + ".", keywords=o.gt_keywords,
                sens=o.sensitivity, action="exclude_duplicate", duplicate_of=f"{ROOT_NAME}/{src}", tags=["duplicate_exact"], date=o.nominal_date)



def build_archives():
    # 1. zip of field photos (plain)
    src_dir = ROOT / f"{PBS}/field_photos/2020"
    rel = f"{PBS}/LabDrive_copy/field_photos_2020_for_Rafael.zip"
    with zipfile.ZipFile(reg.p(rel), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src_dir.rglob("*.JPG")):
            z.write(f, f.relative_to(src_dir.parent))
    reg.add(rel, "high", "Field photographs (zipped copy for collaborator)", lane="archive", fmt="zip", date="2020-08-01",
            title="ZIP of 2020 field photographs sent to collaborator",
            summary="ZIP archive of the 2020 field photographs (MLP, BRF, HCP burst); members duplicate files already in field_photos/2020.",
            keywords=["zip", "field photographs", "duplicates"], sens=("sensitive_location",), action="expand_container",
            tags=["container", "contains_duplicates"])
    for f in sorted(src_dir.rglob("*.JPG")):
        member = str(f.relative_to(src_dir.parent))
        o = reg.labels[f"{ROOT_NAME}/{f.relative_to(ROOT)}"]
        reg.add(member, o.relevance, o.relevance_rationale, lane="image", fmt="jpeg", title=o.gt_title, summary=o.gt_summary,
                keywords=o.gt_keywords, sens=o.sensitivity, container=f"{ROOT_NAME}/{rel}", action="exclude_duplicate",
                duplicate_of=o.path, tags=["archive_member", "duplicate_exact"])
    # 2. tar.gz with nested zip, Windows-illegal names, symlink
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "thesis_backup/ch3").mkdir(parents=True)
        (td / "thesis_backup/ch3/ch3_draft_2022-03-01.txt").write_text(
            "Chapter 3. Does bare ground limit ground-nesting bees? A burn-versus-mow experiment.\n"
            "In 2021 we applied spring burns or mowing to paired plots at CRB and LAF. Nest emergence traps caught "
            "3.2x more Halictidae in burned plots...\n")
        (td / "thesis_backup/notes: todo?.txt").write_text("fix fig 3.2 axis; ask MKA about committee date\n")   # illegal on Windows
        (td / "thesis_backup/ch3/latest.txt").symlink_to("ch3_draft_2022-03-01.txt")
        inner = td / "thesis_backup/figs.zip"
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("fig3_1_emergence.csv", "plot,treatment,halictidae\nCRB1,burn,22\nCRB2,mow,7\nLAF1,burn,18\nLAF2,mow,5\n")
        rel = f"{PBS}/LabDrive_copy/students/Natarajan_thesis_backup_2022-03.tar.gz"
        with tarfile.open(reg.p(rel), "w:gz") as t:
            t.add(td / "thesis_backup", arcname="thesis_backup")
    reg.add(rel, "high", "Dissertation chapters she supervised (backup archive)", lane="archive", fmt="tar.gz (contains nested zip, symlink, Windows-illegal filename)",
            date="2022-03-02", title="Backup archive of Natarajan dissertation chapter 3",
            summary="Gzipped tar of a student's dissertation chapter 3 draft on the burn-versus-mow experiment, a to-do note with a Windows-illegal filename, a symlink, and a nested ZIP of emergence-trap data.",
            keywords=["tar.gz", "dissertation", "nested archive", "burn vs mow"], action="expand_container",
            tags=["container", "nested_archive", "symlink_member", "windows_illegal_name"])
    for name, rel_, t, s in [("thesis_backup/ch3/ch3_draft_2022-03-01.txt", "high", "Dissertation chapter 3 draft (burn vs mow)", "Draft chapter text reporting 3.2x more halictid bees emerging in burned plots."),
                             ("thesis_backup/notes: todo?.txt", "low", "Student to-do note", "Two-item to-do note; filename contains characters illegal on Windows."),
                             ("thesis_backup/ch3/latest.txt", "none", "Symlink to chapter draft", "Symbolic link pointing to the chapter draft; not separate content."),
                             ("thesis_backup/figs.zip", "high", "Nested ZIP of emergence data", "ZIP inside the tarball containing the emergence-trap CSV."),
                             ("thesis_backup/figs.zip::fig3_1_emergence.csv", "high", "Emergence trap counts by treatment", "CSV of halictid emergence counts in burned vs mowed plots at CRB and LAF.")]:
        reg.add(name, rel_, "Dissertation chapters she supervised / original research data", lane="document", title=t, summary=s,
                container=f"{ROOT_NAME}/{rel}", keywords=[], tags=["archive_member"])
    # 3. password-protected zip
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "BRF_exact_locations_DO_NOT_SHARE.csv"
        f.write_text("waypoint,lat,lon,note\nBRF-07,40.55262,-88.01588,affinis colony area\nBRF-09,40.55301,-88.01499,nest search\n")
        rel = f"{PBS}/GIS/restricted/BRF_locations.zip"
        reg.p(rel)
        subprocess.run(["zip", "-j", "-q", "-P", "synthetic-zip-pass", str(ROOT / rel), str(f)], check=True)
    reg.add(rel, "high", "GIS data of survey sites (password-protected, sensitive locations)", lane="archive",
            fmt="zip (ZipCrypto password-protected)", date="2019-06-20", title="Password-protected ZIP of exact remnant locations",
            summary="Encrypted ZIP whose member name indicates exact rusty patched bumble bee locations on the private remnant; contents cannot be read without the password.",
            keywords=["encrypted", "password", "locations"], sens=("sensitive_location",), action="route_human_encrypted",
            tags=["container", "encrypted", "password_protected"])
    # 4. 7z of literature
    rel = "Downloads/old_reprints.7z"
    lit = ROOT / "Documents/Research/Literature"
    subprocess.run(["7z", "a", "-bd", "-y", str(reg.p(rel)), str(lit / "Kremen_2002_PNAS_crop_pollination.pdf"),
                    str(lit / "Smith_2019_soybean_aphid.pdf")], check=True, capture_output=True)
    reg.add(rel, "low", "Unannotated copies of other authors' articles (archived)", lane="archive", fmt="7z", title="7z archive of two reprints",
            summary="7-Zip archive holding duplicate copies of two unannotated reprints from the literature folder.",
            keywords=["7z", "reprints", "duplicates"], action="expand_container", tags=["container", "contains_duplicates"], difficulty="subtle")
    # 5. single-file gzip
    rel = f"{PBS}/data/raw/pantrap_specimens_2016.csv.gz"
    with gzip.open(reg.p(rel), "wb") as g:
        g.write((ROOT / f"{PBS}/data/raw/pantrap_specimens_2016.csv").read_bytes())
    reg.add(rel, "high", "Original research data (compressed copy)", lane="archive", fmt="gzip of CSV", title="Gzipped copy of 2016 pan-trap records",
            summary="Gzip-compressed copy of the 2016 raw specimen CSV; decompressed content duplicates the CSV.", keywords=["gzip", "duplicate"],
            action="expand_container", tags=["container", "contains_duplicates"], difficulty="subtle")
    # 6. high-ratio zip (bomb-guard probe; modest: 200 MB of zeros -> ~200 KB)
    rel = "Downloads/sample_data_DO_NOT_OPEN.zip"
    with zipfile.ZipFile(reg.p(rel), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        with z.open("zeros.bin", "w") as w:
            chunk = b"\x00" * (1 << 20)
            for _ in range(200):
                w.write(chunk)
    reg.add(rel, "none", "Junk download; tests decompression-ratio guard", lane="archive", fmt="zip (expands ~1000x to 200 MB of zeros)",
            title="High-compression-ratio ZIP (bomb-guard probe)",
            summary="ZIP whose single member expands roughly 1000-fold to 200 MB of zero bytes; extractor should enforce ratio/size limits.",
            keywords=["zip bomb", "compression ratio", "guard"], action="route_human_corrupt", tags=["container", "compression_bomb_probe"])


def run():
    build_system(); build_broken_and_misleading(); build_names_and_nesting(); build_duplicates(); build_archives()
    reg.folder("Documents/Research/Prairie_Bee_Survey/LabDrive_copy", "high",
               "Copy of the lab external drive: dataloggers, model outputs, barcodes, GPS, panoramas, instrument files, student backups, nested junk folders.")
