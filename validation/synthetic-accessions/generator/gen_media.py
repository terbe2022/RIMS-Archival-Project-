"""Image and audio/video lanes. Images are procedural illustrations (no real photos),
carrying realistic EXIF (date, camera, GPS) so metadata extraction can be tested."""
from __future__ import annotations

import io
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import reg, rng, SITES

PBS = "Documents/Research/Prairie_Bee_Survey"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(sz, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, sz)


# ------------------------------------------------------------------ drawing primitives
def draw_bee(dr, cx, cy, s, bands=((235, 185, 40), (25, 20, 15)), rusty=False, wings=True):
    if wings:
        dr.ellipse([cx - .2 * s, cy - .75 * s, cx + .5 * s, cy - .1 * s], fill=(220, 230, 240), outline=(120, 130, 140))
        dr.ellipse([cx + .1 * s, cy - .7 * s, cx + .8 * s, cy - .15 * s], fill=(210, 222, 235), outline=(120, 130, 140))
    dr.ellipse([cx - .9 * s, cy - .35 * s, cx - .35 * s, cy + .3 * s], fill=bands[1])          # head
    dr.ellipse([cx - .45 * s, cy - .45 * s, cx + .15 * s, cy + .4 * s], fill=bands[0])         # thorax
    if rusty:
        dr.ellipse([cx - .25 * s, cy - .2 * s, cx - .02 * s, cy + .1 * s], fill=(170, 85, 30))
    dr.ellipse([cx + .05 * s, cy - .4 * s, cx + 1.1 * s, cy + .4 * s], fill=bands[0])          # abdomen
    for i in range(3):
        x = cx + (.25 + .25 * i) * s
        dr.rectangle([x, cy - .38 * s, x + .1 * s, cy + .38 * s], fill=bands[1])
    for i in range(3):
        dr.line([(cx - .3 * s + i * .2 * s, cy + .35 * s), (cx - .4 * s + i * .25 * s, cy + .75 * s)], fill=bands[1], width=max(2, int(s / 18)))
    dr.line([(cx - .85 * s, cy - .3 * s), (cx - 1.15 * s, cy - .7 * s)], fill=bands[1], width=max(2, int(s / 20)))


def draw_flower(dr, x, y, r, color):
    for a in range(0, 360, 30):
        px, py = x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))
        dr.ellipse([px - r * .45, py - r * .45, px + r * .45, py + r * .45], fill=color)
    dr.ellipse([x - r * .4, y - r * .4, x + r * .4, y + r * .4], fill=(90, 60, 30))


def prairie_scene(seed, w=1600, h=1067, bee=None, bowls=False, sky=(150, 190, 235), stage="mature", burned=False):
    r = rng(f"scene{seed}")
    im = Image.new("RGB", (w, h), sky)
    dr = ImageDraw.Draw(im)
    for i in range(h // 2):
        c = tuple(int(sky[j] + (255 - sky[j]) * i / (h / 2) * .4) for j in range(3))
        dr.line([(0, i), (w, i)], fill=c)
    horizon = int(h * (0.42 + r.uniform(-.05, .05)))
    dr.rectangle([0, horizon, w, h], fill=(120, 110, 70) if burned else (96, 130, 62))
    density = {"young": 400, "mature": 1500, "remnant": 2200}[stage]
    for _ in range(density):
        x = r.randint(0, w); yb = r.randint(horizon, h)
        ht = r.randint(20, 160) * (yb - horizon) / (h - horizon + 1) + 10
        col = (r.randint(60, 110), r.randint(110, 160), r.randint(40, 70)) if not burned else (60, 50, 40)
        dr.line([(x, yb), (x + r.randint(-15, 15), yb - ht)], fill=col, width=r.randint(1, 3))
    if not burned:
        for _ in range({"young": 15, "mature": 70, "remnant": 140}[stage]):
            x = r.randint(0, w); y = r.randint(horizon + 20, h)
            draw_flower(dr, x, y, r.randint(6, 20) * (y - horizon) / (h - horizon) + 3,
                        r.choice([(186, 110, 200), (240, 200, 40), (230, 120, 170), (250, 250, 240)]))
    if bowls:
        for i, c in enumerate([(40, 90, 230), (250, 220, 20), (245, 245, 245)] * 2):
            x = 300 + i * 180; y = int(h * .8)
            dr.ellipse([x, y, x + 110, y + 45], fill=c, outline=(40, 40, 40), width=3)
    if bee:
        draw_bee(dr, w * .55, h * .55, bee.get("size", 160), rusty=bee.get("rusty", False))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    return im


def specimen_plate(taxon, sid, seed, rusty=False, w=2000, h=1500):
    r = rng(f"spec{seed}")
    im = Image.new("RGB", (w, h), (248, 248, 246))
    dr = ImageDraw.Draw(im)
    bands = ((235, 185, 40), (25, 20, 15))
    if taxon.startswith(("Agapostemon", "Augochlor")):
        bands = ((60, 170, 90), (30, 90, 50))
    elif taxon.startswith(("Lasioglossum", "Ceratina", "Hylaeus")):
        bands = ((40, 40, 45), (15, 15, 20))
    elif taxon.startswith("Andrena"):
        bands = ((120, 90, 60), (35, 25, 20))
    draw_bee(dr, w * .45, h * .45, 380 + r.randint(-40, 40), bands=bands, rusty=rusty)
    dr.line([(w * .1, h * .45), (w * .85, h * .45)], fill=(150, 150, 150), width=4)    # pin
    dr.rectangle([w * .08, h * .82, w * .08 + 500, h * .82 + 18], fill=(0, 0, 0))     # scale bar
    dr.text((w * .08, h * .86), "5 mm", fill=(0, 0, 0), font=font(36))
    dr.rectangle([w * .6, h * .75, w * .95, h * .95], outline=(0, 0, 0), width=3, fill=(255, 255, 250))
    dr.text((w * .62, h * .77), sid, font=font(34, True), fill=(0, 0, 0))
    dr.text((w * .62, h * .83), taxon, font=font(32), fill=(0, 0, 0))
    dr.text((w * .62, h * .89), "det. P. Natarajan", font=font(28), fill=(0, 0, 0))
    return im


def exif_bytes(dt, make="Canon", model="EOS 80D", lat=None, lon=None, desc=None):
    ex = Image.Exif()
    ex[0x010F] = make; ex[0x0110] = model; ex[0x0132] = dt
    if desc:
        ex[0x010E] = desc
    ifd = ex.get_ifd(0x8769); ifd[0x9003] = dt
    if lat is not None:
        def dms(v):
            from PIL.TiffImagePlugin import IFDRational
            v = abs(v); d = int(v); m = int((v - d) * 60); s = round(((v - d) * 60 - m) * 60 * 100)
            return (IFDRational(d, 1), IFDRational(m, 1), IFDRational(s, 100))
        gps = ex.get_ifd(0x8825)
        gps[1] = "N" if lat >= 0 else "S"; gps[2] = dms(lat)
        gps[3] = "E" if lon >= 0 else "W"; gps[4] = dms(lon)
    return ex


def save_jpg(im, rel, dt, gps=None, model="EOS 80D", make="Canon", desc=None, quality=88):
    ex = exif_bytes(dt, make, model, *(gps or (None, None)), desc=desc)
    im.save(reg.p(rel), "JPEG", quality=quality, exif=ex.tobytes())


# ------------------------------------------------------------------ images
def build_images():
    P = f"{PBS}/field_photos"
    site = {s[0]: s for s in SITES}
    photo_specs = [
        ("SBP", "2019-06-16", "mature", False, None, "SBP transect 1 facing north, mature restoration with dense bergamot"),
        ("LAF", "2019-06-17", "young", False, None, "LAF 3-year-old planting, sparse bloom, weedy"),
        ("MLP", "2020-07-12", "mature", True, None, "Pan-trap bowls (blue, yellow, white) set at Meadowlark Prairie station 2"),
        ("KRR", "2021-04-20", "mature", False, None, "Kickapoo Ridge after spring prescribed burn"),
        ("BRF", "2019-06-15", "remnant", False, {"size": 130, "rusty": True}, "Rusty patched bumble bee on wild bergamot at the remnant"),
        ("BRF", "2020-07-08", "remnant", True, None, "Pan-trap station on the never-plowed remnant, very high forb density"),
        ("HCP", "2018-08-09", "mature", False, {"size": 110}, "Bumble bee on prairie at Hollis Creek, late summer"),
        ("CRB", "2022-06-14", "young", True, None, "New planting at Cardinal Bluff with pan traps in bare soil"),
    ]
    for i, (code, date, stage, bowls, bee, desc) in enumerate(photo_specs):
        burned = "burn" in desc
        im = prairie_scene(i, bee=bee, bowls=bowls, stage=stage, burned=burned)
        y, m, d = date.split("-")
        rel = f"{P}/{y}/{code}/IMG_{4000 + i * 37:04d}.JPG"
        lat, lon = site[code][4] + .0004, site[code][5] - .0003
        save_jpg(im, rel, f"{y}:{m}:{d} 10:{10 + i:02d}:00", gps=(lat, lon), desc=None)
        sens = ("sensitive_location",) if code == "BRF" else ("none",)
        reg.add(rel, "high", "Field photographs of the survey sites", lane="image", fmt="jpeg (EXIF date, camera, GPS)",
                date=date, title=f"Field photograph: {desc}",
                summary=f"Field photograph ({site[code][1]}, {date}): {desc}. EXIF records camera and GPS coordinates" +
                        (" that reveal the private remnant location." if code == "BRF" else "."),
                keywords=["field photograph", site[code][1], "prairie", "EXIF GPS"] + (["Bombus affinis"] if bee and bee.get("rusty") else []),
                sens=sens, tags=["exif_gps", "camera_filename"], difficulty="obvious" if bee or bowls else "subtle")
    # burst near-duplicates (perceptual dedupe)
    base = prairie_scene(99, bee={"size": 150}, stage="mature")
    for k in range(4):
        im = base.copy().transform(base.size, Image.AFFINE, (1, 0, k * 3, 0, 1, k * 2))
        im = im.point(lambda v, k=k: min(255, int(v * (1 + .015 * k))))
        rel = f"{P}/2020/HCP/burst/IMG_5{k:03d}.JPG"
        save_jpg(im, rel, f"2020:07:14 11:02:0{k}", gps=(40.2513, -88.1907))
        reg.add(rel, "high", "Field photographs (burst sequence)", lane="image", fmt="jpeg", date="2020-07-14",
                title=f"Burst frame {k + 1} of 4: bee on flowers at Hollis Creek",
                summary="One of four near-identical burst frames of a bee on prairie flowers; candidates for perceptual near-duplicate review (keep one).",
                keywords=["burst", "near duplicate", "field photograph"],
                action="appraise" if k == 0 else "review_near_duplicate", tags=["near_duplicate"], difficulty="subtle")
    # specimen plates (TIFF high-res + JPEG derivative)
    S = f"{PBS}/specimen_images"
    for i, (taxon, rusty) in enumerate([("Bombus affinis", True), ("Andrena commoda", False), ("Agapostemon virescens", False),
                                        ("Lasioglossum pilosum", False), ("Calliopsis andreniformis", False), ("Melissodes trinodis", False)]):
        sid = f"PBS-2019-{1200 + i * 211:06d}"
        im = specimen_plate(taxon, sid, i, rusty)
        rel = f"{S}/tiff_masters/{sid}_{taxon.replace(' ', '_')}.tif"
        im.save(reg.p(rel), "TIFF", compression="tiff_lzw", dpi=(600, 600))
        reg.add(rel, "high", "Photographs or images of bee specimens", lane="image", fmt="tiff (LZW, 600 dpi)",
                date="2020-02-10", title=f"Specimen image master: {taxon} {sid}",
                summary=f"High-resolution specimen plate of a pinned {taxon} with scale bar and determination label {sid}.",
                keywords=["specimen image", taxon, "voucher", "TIFF"])
        rel2 = f"{S}/web/{sid}.jpg"
        im.resize((800, 600)).save(reg.p(rel2), "JPEG", quality=80)
        reg.add(rel2, "high", "Images of bee specimens (web derivative)", lane="image", fmt="jpeg (derivative)",
                date="2020-02-12", title=f"Specimen image web copy: {taxon}",
                summary=f"Reduced JPEG derivative of the {taxon} specimen plate; same content as its TIFF master.",
                keywords=["specimen image", taxon, "derivative"], tags=["derivative_of_master"], difficulty="subtle")
    # Huge panorama TIFF (large-file + downsampling)
    big = prairie_scene(200, w=6000, h=2600, stage="remnant")
    rel = f"{PBS}/LabDrive_copy/panoramas/BRF_north_pasture_panorama_2021_stitched.tif"
    big.save(reg.p(rel), "TIFF")    # uncompressed ~47 MB
    reg.add(rel, "high", "Field photographs of the survey sites (large stitched panorama)", lane="image",
            fmt="tiff (uncompressed, 6000x2600, ~47 MB)", date="2021-07-02",
            title="Stitched panorama of the Ritter remnant north pasture",
            summary="Very large uncompressed panorama of dense remnant prairie; tests downsampling before vision model input.",
            keywords=["panorama", "remnant", "large image"], sens=("sensitive_location",), tags=["large_file", "needs_downsample"])
    # whiteboard photo (ambiguous, text in image)
    im = Image.new("RGB", (1600, 1100), (232, 234, 230)); dr = ImageDraw.Draw(im)
    dr.rectangle([60, 60, 1540, 1040], fill=(250, 250, 248), outline=(150, 150, 150), width=8)
    for j, (t, c) in enumerate([("richness ~ s(age) + (1|site)", (20, 20, 160)), ("offset(log bowl-days) !!", (180, 20, 20)),
                                ("specialists: no plateau?", (20, 120, 20)), ("BRF = reference, not a point", (20, 20, 20)),
                                ("bare ground > flowers?  test w/ Jonah quadrats", (20, 20, 160))]):
        dr.text((120, 120 + j * 160), t, font=font(58), fill=c)
    dr.line([(1100, 900), (1450, 500)], fill=(20, 20, 20), width=6)
    im = im.rotate(-2.5, fillcolor=(200, 200, 200)).filter(ImageFilter.GaussianBlur(1.2))
    rel = "Pictures/Phone/IMG_20200410_154455.jpg"
    save_jpg(im, rel, "2020:04:10 15:44:55", make="Google", model="Pixel 3a")
    reg.add(rel, "high", "Records showing how the analysis developed (whiteboard of model planning)", lane="image",
            fmt="jpeg (phone photo of text)", date="2020-04-10",
            title="Phone photo of whiteboard planning the richness models",
            summary="Photo of a whiteboard listing the GAM formula, effort offset, the open question of specialist plateau, treating BRF as reference, and testing bare ground with quadrat data.",
            keywords=["whiteboard", "analysis planning", "OCR in image"], tags=["text_in_image", "needs_ocr"], difficulty="ambiguous")
    # Screenshot
    im = Image.new("RGB", (1440, 900), (40, 44, 52)); dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, 1440, 28], fill=(220, 220, 220))
    for j, t in enumerate(["> summary(m_spec)", "Approximate significance of smooth terms:",
                           "            edf Ref.df Chi.sq  p-value", "s(age_c)  1.04   1.08  21.7  4.1e-06 ***",
                           "s(site)   5.11   9.00  14.2  0.0019 **", "R-sq.(adj) = 0.71   Deviance explained = 74.3%"]):
        dr.text((30, 60 + j * 40), t, font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 26), fill=(200, 230, 200))
    rel = "Desktop/Screenshot 2020-11-12 at 3.22.10 PM.png"
    im.save(reg.p(rel))
    reg.add(rel, "high", "Analysis outputs (screenshot of model summary)", lane="image", fmt="png (screenshot)",
            date="2020-11-12", title="Screenshot of R model summary for specialist richness",
            summary="Screenshot of an R console showing the GAM summary for specialist richness (near-linear age smooth, p < 0.001, deviance explained 74%).",
            keywords=["screenshot", "R output", "model summary"], tags=["text_in_image", "screenshot"], difficulty="subtle")
    # Home garden bee photo (ambiguous personal/research)
    im = prairie_scene(300, w=1200, h=900, bee={"size": 120}, stage="young", sky=(170, 200, 230))
    rel = "Pictures/Phone/IMG_20210703_081210.jpg"
    save_jpg(im, rel, "2021:07:03 08:12:10", gps=(40.1102, -88.2201), make="Google", model="Pixel 3a")
    reg.add(rel, "low", "Personal photograph, but of a bee; not from a survey site", lane="image", fmt="jpeg (phone, GPS = home)",
            date="2021-07-03", title="Phone photo of a bee in a home garden",
            summary="Personal phone photo of a bumble bee on garden flowers taken at a residential location, not a survey site; EXIF GPS points to the donor's home.",
            keywords=["garden", "bee", "personal photo"], sens=("pii_contact",), tags=["exif_gps"], difficulty="ambiguous")
    # Family photos (none)
    for k, (scene, dt) in enumerate([("birthday", "2018:05:12 18:30:00"), ("lake", "2019:08:03 14:00:00"), ("dog", "2021:12:25 09:15:00")]):
        im = Image.new("RGB", (1200, 900), [(250, 220, 200), (120, 170, 220), (200, 180, 160)][k]); dr = ImageDraw.Draw(im)
        if scene == "birthday":
            dr.rectangle([450, 450, 750, 650], fill=(250, 250, 250)); dr.rectangle([450, 430, 750, 470], fill=(240, 120, 160))
            for c in range(5):
                dr.rectangle([480 + c * 55, 360, 490 + c * 55, 430], fill=(100, 160, 240)); dr.ellipse([477 + c * 55, 335, 493 + c * 55, 360], fill=(255, 190, 40))
        elif scene == "lake":
            dr.rectangle([0, 500, 1200, 900], fill=(40, 90, 160)); dr.polygon([(500, 520), (700, 520), (650, 580), (550, 580)], fill=(150, 80, 40))
        else:
            dr.ellipse([400, 400, 800, 700], fill=(120, 80, 40)); dr.ellipse([700, 300, 900, 480], fill=(120, 80, 40)); dr.ellipse([820, 360, 840, 380], fill=(0, 0, 0))
        rel = f"Pictures/Family/{2018 + k}/IMG_{7000 + k}.jpg"
        save_jpg(im, rel, dt, make="Apple", model="iPhone 8")
        reg.add(rel, "none", "Family photographs and personal media", lane="image", fmt="jpeg", date=dt[:10].replace(":", "-"),
                title=f"Family photo: {scene}", summary=f"Personal family snapshot ({scene}) unrelated to university work.",
                keywords=["family photo", scene, "personal"], sens=("minor_child",) if scene == "birthday" else ("none",))
    # Format variety: webp, gif (animated), bmp, eps, ico-like, png with alpha
    im = specimen_plate("Bombus impatiens", "PBS-2018-000777", 50).resize((900, 675))
    im.save(reg.p(f"{PBS}/specimen_images/web/PBS-2018-000777.webp"), "WEBP", quality=80)
    reg.add(f"{PBS}/specimen_images/web/PBS-2018-000777.webp", "high", "Images of bee specimens", lane="image", fmt="webp",
            title="Specimen image: Bombus impatiens (WebP)", summary="WebP specimen plate of a pinned common eastern bumble bee with scale bar and label.",
            keywords=["specimen image", "Bombus impatiens", "WebP"], difficulty="subtle")
    frames = [prairie_scene(400 + f, w=480, h=320, bee={"size": 40 + f * 4}, stage="mature") for f in range(6)]
    frames[0].save(reg.p("Documents/Talks/media/bee_approach_animation.gif"), save_all=True, append_images=frames[1:], duration=300, loop=0)
    reg.add("Documents/Talks/media/bee_approach_animation.gif", "moderate", "Media used in talks presenting the research",
            lane="image", fmt="gif (animated, 6 frames)", title="Animated GIF of a bee approaching for a talk",
            summary="Six-frame animated illustration of a bee growing larger over a prairie, used as a slide animation.",
            keywords=["animation", "GIF", "talk media"], tags=["animated"], difficulty="ambiguous")
    prairie_scene(500, w=640, h=480).save(reg.p("Old_Computer_Backup_2009/My Documents/My Pictures/hollis_creek_2007.bmp"))
    reg.add("Old_Computer_Backup_2009/My Documents/My Pictures/hollis_creek_2007.bmp", "moderate",
            "Early field photograph of a future survey site (lab history)", lane="image", fmt="bmp (legacy bitmap)", date="2007-07-01",
            title="2007 photograph of Hollis Creek Prairie (BMP)", summary="Legacy uncompressed bitmap of a prairie scene labelled as Hollis Creek in 2007, before the survey began.",
            keywords=["legacy format", "BMP", "Hollis Creek"], tags=["legacy_format"], difficulty="ambiguous")
    logo = Image.new("RGBA", (600, 600), (0, 0, 0, 0)); dr = ImageDraw.Draw(logo)
    dr.ellipse([20, 20, 580, 580], fill=(250, 240, 210, 255), outline=(60, 100, 40, 255), width=14)
    draw_bee(dr, 270, 320, 150); dr.text((120, 470), "Achterberg Lab", font=font(48, True), fill=(60, 100, 40, 255))
    logo.save(reg.p("Documents/Lab_Admin/branding/lab_logo_transparent.png"))
    reg.add("Documents/Lab_Admin/branding/lab_logo_transparent.png", "moderate", "Records documenting the lab's history (lab logo)",
            lane="image", fmt="png (RGBA transparency)", title="Achterberg Lab logo", summary="Round lab logo with a stylised bee and the lab name on a transparent background.",
            keywords=["logo", "branding", "lab"], tags=["alpha_channel"], difficulty="ambiguous")
    logo.convert("RGB").save(reg.p("Documents/Lab_Admin/branding/lab_logo_print.eps"))
    reg.add("Documents/Lab_Admin/branding/lab_logo_print.eps", "moderate", "Lab logo, print version", lane="image",
            fmt="eps (Encapsulated PostScript)", title="Achterberg Lab logo (EPS print version)",
            summary="Encapsulated PostScript version of the lab logo for print.", keywords=["logo", "EPS"],
            tags=["same_content_different_format"], difficulty="ambiguous")
    reg.folder(f"{PBS}/field_photos", "high", "Field photographs by year and site with EXIF GPS, including a burst sequence of near-duplicates.")
    reg.folder(f"{PBS}/specimen_images", "high", "Specimen image TIFF masters and JPEG/WebP web derivatives.")
    reg.folder("Pictures", "low", "Pictures folder: phone photos (whiteboard, garden bee) and family photographs.")
    reg.folder("Pictures/Family", "none", "Family snapshots unrelated to university work.")


# ------------------------------------------------------------------ audio / video
def tts(text, wav, voice="en-us", speed=150, pitch=50):
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-p", str(pitch), "-w", str(wav), text], check=True,
                   capture_output=True)


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


INTERVIEW = [
    ("en-us+m3", "This is Miriam Achterberg. It is July ninth, twenty nineteen, and I am with Harold Ritter at his farm in Ford County. Harold, tell me about the north pasture."),
    ("en-us+m7", "My grandfather bought the place in nineteen eleven. The north forty was too wet to plow with horses, so it never got broke. Dad ran a few cows on it after the war."),
    ("en-us+m3", "And when did you start burning it?"),
    ("en-us+m7", "About nineteen seventy five. June's father said fire is what kept it in flowers. We burn every three or four years, in the spring, when the wind is right."),
    ("en-us+m3", "Did you ever notice the bumble bees?"),
    ("en-us+m7", "There were always bumble bees. I couldn't tell you what kind. Your students say one of them is rare now. We would like to keep it that way, quiet, if you understand me."),
]


def build_av():
    A = f"{PBS}/oral_history"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); parts = []
        for i, (voice, line) in enumerate(INTERVIEW):
            w = td / f"p{i}.wav"; tts(line, w, voice=voice, speed=140 + (i % 2) * 10); parts.append(w)
        lst = td / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
        full = td / "full.wav"
        ff("-f", "concat", "-safe", "0", "-i", str(lst), "-af", "aresample=44100", str(full))
        rel = f"{A}/Ritter_interview_2019-07-09.wav"
        ff("-i", str(full), "-ar", "44100", "-ac", "1", str(reg.p(rel)))
        reg.add(rel, "high", "Oral-history or interview material about the history of the sites", lane="av",
                fmt="wav (PCM, speech)", date="2019-07-09", title="Oral history interview with landowner Harold Ritter",
                summary="Recorded interview in which the landowner recounts that the north pasture was never plowed since 1911, was lightly grazed, and has been burned every 3-4 years since about 1975, and asks that the rare bee be kept quiet.",
                keywords=["oral history", "interview", "land history", "speech", "transcription"],
                sens=("sensitive_location", "pii_contact"), tags=["audio_speech", "needs_transcription"])
        mp3 = f"{A}/Ritter_interview_2019-07-09_access_copy.mp3"
        ff("-i", str(full), "-codec:a", "libmp3lame", "-b:a", "96k", "-id3v2_version", "3",
           "-metadata", "title=Ritter interview access copy", "-metadata", "artist=M. Achterberg", str(reg.p(mp3)))
        reg.add(mp3, "high", "Oral-history material (access derivative)", lane="av", fmt="mp3 (ID3 tags)", date="2019-07-10",
                title="Oral history interview with Harold Ritter (MP3 access copy)",
                summary="Compressed access copy of the landowner interview; same audio content as the WAV master.",
                keywords=["oral history", "MP3", "derivative"], sens=("sensitive_location", "pii_contact"),
                tags=["audio_speech", "derivative_of_master"], difficulty="subtle")
        # voice memo (m4a)
        w = td / "memo.wav"
        tts("Note to self. Lab meeting idea. If the ground nesters are limited by bare soil, we should set up a burn versus mow experiment at Cardinal Bluff and Lafayette Road next spring. Ask Karen about permits.", w, voice="en-us+f3")
        rel = "Documents/Research/Prairie_Bee_Survey/voice_memos/memo_2021-03-02.m4a"
        ff("-i", str(w), "-c:a", "aac", "-b:a", "64k", str(reg.p(rel)))
        reg.add(rel, "high", "Records showing research planning (spoken note about an experiment)", lane="av", fmt="m4a (AAC, speech)",
                date="2021-03-02", title="Voice memo proposing burn-versus-mow experiment",
                summary="Spoken memo proposing a burn versus mow experiment at two young plantings to test whether bare soil limits ground-nesting bees, and to ask DNR about permits.",
                keywords=["voice memo", "experiment design", "bare ground", "speech"], tags=["audio_speech", "needs_transcription"], difficulty="subtle")
        # voicemail from reporter (moderate)
        w = td / "vm.wav"
        tts("Hi Professor Achterberg, this is Lena Ortiz from the Champaign Courier, following up on my email about the prairie plantings story. You can reach me at five five five, oh one nine eight. Thanks.", w, voice="en-us+f2")
        rel = "Documents/Talks/media/voicemail_courier_2021-07-13.wav"
        ff("-i", str(w), "-ar", "8000", "-ac", "1", str(reg.p(rel)))
        reg.add(rel, "low", "Media request logistics (voicemail), not the research itself", lane="av", fmt="wav (8 kHz telephone)",
                date="2021-07-13", title="Voicemail from newspaper reporter",
                summary="Telephone-quality voicemail from a reporter following up on an interview request and leaving a callback number.",
                keywords=["voicemail", "media", "speech"], sens=("pii_contact",), tags=["audio_speech", "needs_transcription"], difficulty="ambiguous")
        # music (none)
        rel = "Music/iTunes/Unknown Artist/Prairie Winds (instrumental).mp3"
        ff("-f", "lavfi", "-i", "sine=frequency=440:duration=8", "-f", "lavfi", "-i", "sine=frequency=554:duration=8",
           "-filter_complex", "amix=inputs=2", "-codec:a", "libmp3lame", "-b:a", "128k",
           "-metadata", "title=Prairie Winds", "-metadata", "genre=Folk", str(reg.p(rel)))
        reg.add(rel, "none", "Personal media such as music libraries (title deceptively mentions prairie)", lane="av",
                fmt="mp3 (tones, music metadata)", title="Music track 'Prairie Winds'",
                summary="Personal music library track (synthetic tones) whose title mentions prairie but contains no research content.",
                keywords=["music", "personal media"], difficulty="subtle", tags=["misleading_title"])
        # Video: field timelapse with captions + narration (mp4), drone-like pan (mov), long low-motion video
        frames = td / "frames"; frames.mkdir()
        for i in range(24):
            im = prairie_scene(600 + i % 3, w=1280, h=720, bowls=True, bee={"size": 60 + i * 3} if i > 8 else None, stage="mature")
            ImageDraw.Draw(im).text((30, 670), f"MLP station 2  2020-07-12  {9 + i // 6}:{(i % 6) * 10:02d}", font=font(30), fill=(255, 255, 255))
            im.save(frames / f"f{i:03d}.png")
        nar = td / "nar.wav"
        tts("Time lapse of pan traps at Meadowlark Prairie station two. Bowls set at eight thirty. Watch for bees visiting the blue bowls after nine.", nar, voice="en-us+f3")
        rel = f"{PBS}/video/MLP_pantrap_timelapse_2020-07-12.mp4"
        ff("-framerate", "4", "-i", str(frames / "f%03d.png"), "-i", str(nar), "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", "-metadata", "title=MLP pan trap timelapse", str(reg.p(rel)))
        reg.add(rel, "high", "Recordings presenting the research (field timelapse with narration)", lane="av",
                fmt="mp4 (H.264 + AAC narration)", date="2020-07-12", title="Pan-trap timelapse video at Meadowlark Prairie",
                summary="Short narrated timelapse of coloured pan-trap bowls at Meadowlark Prairie with an on-screen timestamp, showing bees arriving after 9 am.",
                keywords=["video", "timelapse", "pan trap", "narration"], tags=["video", "audio_speech", "text_in_video"])
        rel = f"{PBS}/video/DJI_0042.MOV"
        ff("-f", "lavfi", "-i", "color=c=green:s=1920x1080:d=6", "-loop", "1", "-i", str(frames / "f005.png"),
           "-filter_complex", "[1:v]scale=3840:2160,crop=1920:1080:x='t*300':y=400[v]", "-map", "[v]", "-t", "6",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-metadata", "make=DJI", "-metadata", "creation_time=2021-06-30T14:00:00Z", str(reg.p(rel)))
        reg.add(rel, "high", "Recordings of the survey sites (aerial pan)", lane="av", fmt="mov (QuickTime, H.264 1080p, no audio)",
                date="2021-06-30", title="Drone-style aerial pan over a survey site (no audio)",
                summary="Six-second 1080p silent video panning across a prairie with pan-trap bowls; camera-named file with no descriptive title.",
                keywords=["video", "aerial", "drone", "no audio"], tags=["video", "camera_filename", "keyframes_needed"], difficulty="subtle")
        rel = f"{PBS}/LabDrive_copy/raw_video/lab_meeting_2021-02-18_zoom_recording.mp4"
        slides = td / "slide.png"
        im = Image.new("RGB", (1280, 720), (30, 30, 30)); dr = ImageDraw.Draw(im)
        dr.text((80, 300), "Lab meeting - Feb 18 2021 - barcoding backlog & 2021 field plan", font=font(40), fill=(230, 230, 230))
        im.save(slides)
        sp = td / "sp.wav"
        tts("Okay, let's start. First item, barcoding. We still have six hundred Lasioglossum waiting. Second item, the field plan for twenty twenty one. Priya takes the northern sites, Jonah the southern ones.", sp, voice="en-us+m3")
        ff("-loop", "1", "-i", str(slides), "-i", str(sp), "-f", "lavfi", "-i", "anoisesrc=d=180:c=pink:a=0.002",
           "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest[a]", "-map", "0:v", "-map", "[a]", "-t", "180",
           "-c:v", "libx264", "-tune", "stillimage", "-r", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "48k", str(reg.p(rel)))
        reg.add(rel, "high", "Recordings presenting and planning the research (lab meeting)", lane="av",
                fmt="mp4 (3 min, static slide, speech then silence)", date="2021-02-18",
                title="Recorded lab meeting on barcoding backlog and field plan",
                summary="Three-minute video recording of a lab meeting: one static title slide, about 15 seconds of speech on the barcoding backlog and site assignments, then near-silent background noise; tests long-media sampling.",
                keywords=["lab meeting", "recording", "barcoding", "field plan"], tags=["video", "audio_speech", "long_mostly_silent"], difficulty="subtle")
        rel = "Downloads/funny_cat_compilation.webm"
        ff("-f", "lavfi", "-i", "testsrc=size=640x360:rate=15:duration=5", "-c:v", "libvpx", "-b:v", "300k", str(reg.p(rel)))
        reg.add(rel, "none", "Personal media unrelated to university work", lane="av", fmt="webm (VP8 test pattern)",
                title="Downloaded video titled 'funny cat compilation'",
                summary="Downloaded personal video (test-pattern content) unrelated to research; title suggests entertainment.",
                keywords=["video", "personal", "entertainment"], tags=["video"])
    reg.folder(f"{PBS}/oral_history", "high", "Landowner oral-history interview: WAV master and MP3 access copy.")
    reg.folder(f"{PBS}/video", "high", "Field video: narrated pan-trap timelapse and aerial pan.")
    reg.folder("Music", "none", "Personal music library.")


def run():
    build_images(); build_av()
