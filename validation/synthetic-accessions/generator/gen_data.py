"""Tabular, scientific, geospatial, database and code lanes."""
from __future__ import annotations

import csv
import io
import json
import sqlite3
from pathlib import Path

import h5py
import nbformat
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import scipy.io
import shapefile
from openpyxl import Workbook

import charts
from common import reg, rng, SITES, BEE_TAXA, ROOT
from survey import specimens, SPEC_HEADER, richness_table, YEARS, ROUNDS, STATIONS

PBS = "Documents/Research/Prairie_Bee_Survey"
LD = f"{PBS}/LabDrive_copy"


def write_csv(rel, header, rows):
    with open(reg.p(rel), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(header); w.writerows(rows)


def build_tabular():
    sp = specimens()
    for y in YEARS:
        rel = f"{PBS}/data/raw/pantrap_specimens_{y}.csv"
        write_csv(rel, SPEC_HEADER, [s for s in sp if s[2] == y])
        reg.add(rel, "high", "Original research data: raw pan-trap records", lane="tabular", fmt="text/csv",
                date=f"{y}-09-30", title=f"Raw pan-trap specimen records, {y} season",
                summary=f"Specimen-level pan-trap records for the {y} season across ten sites: ID, site, date, round, station, bowl colour, taxon, sex, barcoding status and determiner."
                        + (" Includes rusty patched bumble bee records at BRF." if y >= 2019 else ""),
                keywords=["pan trap", "specimen data", "raw data", str(y)],
                sens=("sensitive_location",) if y >= 2019 else ("none",), tags=["series"])
    # Full combined file (also inside the sqlite DB)
    rel = f"{PBS}/data/processed/PBS_specimens_2016-2022_ALL.csv"
    write_csv(rel, SPEC_HEADER, sp)
    reg.add(rel, "high", "Original research data: compiled specimen database export", lane="tabular", fmt="text/csv",
            date="2023-01-15", title="Compiled specimen records 2016-2022",
            summary=f"All {len(sp):,} specimen records from the 2016-2022 Prairie Bee Survey in one table; union of the yearly raw files.",
            keywords=["specimen database", "compiled data", "Darwin Core"], sens=("sensitive_location",))
    write_csv(f"{PBS}/data/processed/richness_by_site_year.csv",
              ["site", "year", "years_since_restoration", "richness", "specialist_richness", "abundance"],
              richness_table())
    reg.add(f"{PBS}/data/processed/richness_by_site_year.csv", "high", "Processed research data behind the published results",
            lane="tabular", fmt="text/csv", date="2023-01-15", title="Bee richness by site and year (analysis table)",
            summary="Derived table of species richness, specialist richness and abundance for each site-year with years since restoration, the input to the GAM models.",
            keywords=["richness", "analysis table", "restoration age"])
    # floral + bare ground quadrats
    r = rng("quad")
    rows = []
    for code, *_rest in SITES:
        for y in (2019, 2020, 2021, 2022):
            for st in STATIONS:
                for q in range(1, 7):
                    rows.append([code, y, st, q, r.randint(0, 45) if code != "BRF" else r.randint(18, 50),
                                 r.randint(0, 60), r.choice(["Monarda fistulosa", "Dalea purpurea", "Rudbeckia hirta",
                                                              "Echinacea pallida", "Pycnanthemum virginianum", "Solidago rigida"])])
    write_csv(f"{PBS}/data/raw/floral_bareground_quadrats_2019-2022.csv",
              ["site", "year", "station", "quadrat", "pct_bare_ground", "flower_stems_m2", "dominant_bloom"], rows)
    reg.add(f"{PBS}/data/raw/floral_bareground_quadrats_2019-2022.csv", "high", "Original research data: floral surveys",
            lane="tabular", fmt="text/csv", date="2022-09-01", title="Floral resource and bare-ground quadrat data 2019-2022",
            summary="Quadrat measurements of percent bare ground, flower stem density and dominant blooming species at each station, 2019-2022.",
            keywords=["floral survey", "bare ground", "quadrats", "habitat"])
    # site metadata JSON
    meta = [{"code": c, "name": n, "county": co, "restored": None if c == "BRF" else y, "lat": la, "lon": lo,
             "ownership": ow, "remnant": c == "BRF"} for c, n, co, y, la, lo, ow in SITES]
    reg.p(f"{PBS}/data/site_metadata.json").write_text(json.dumps({"survey": "Prairie Bee Survey", "sites": meta}, indent=2))
    reg.add(f"{PBS}/data/site_metadata.json", "high", "Original research data: site metadata", lane="tabular",
            fmt="application/json", title="Survey site metadata (JSON)",
            summary="Names, counties, restoration years, ownership and exact coordinates of the ten survey sites including the private remnant.",
            keywords=["site metadata", "coordinates", "JSON"], sens=("sensitive_location",))
    # EML XML metadata
    eml = ("<?xml version=\"1.0\"?>\n<eml:eml xmlns:eml=\"eml://ecoinformatics.org/eml-2.1.1\" packageId=\"pbs.1.1\">\n"
           "<dataset><title>Prairie Bee Survey specimen data 2016-2022 (SYNTHETIC)</title>\n"
           "<creator><individualName><surName>Achterberg</surName></individualName></creator>\n"
           "<abstract><para>Pan-trap and netting records of wild bees at nine restored and one remnant prairie.</para></abstract>\n"
           "<coverage><geographicCoverage><geographicDescription>East-central Illinois; BRF generalised to Ford County"
           "</geographicDescription></geographicCoverage><temporalCoverage><rangeOfDates><beginDate><calendarDate>2016-05-20"
           "</calendarDate></beginDate><endDate><calendarDate>2022-08-09</calendarDate></endDate></rangeOfDates></temporalCoverage></coverage>\n"
           "</dataset></eml:eml>\n")
    reg.p(f"{PBS}/data/metadata/PBS_specimens_EML.xml").write_text(eml)
    reg.add(f"{PBS}/data/metadata/PBS_specimens_EML.xml", "high", "Original research data documentation (metadata)",
            lane="document", fmt="application/xml (EML 2.1.1)", title="Ecological Metadata Language record for the specimen data",
            summary="EML XML metadata describing the specimen dataset: title, creator, abstract, geographic coverage generalising the remnant to county, and 2016-2022 temporal coverage.",
            keywords=["EML", "metadata", "XML", "data deposit"], difficulty="subtle")
    # ambiguous unlabeled spreadsheet
    wb = Workbook(); ws = wb.active
    r = rng("misc")
    for i in range(30):
        ws.append([r.randint(1, 40), r.choice(["b", "y", "w"]), round(r.uniform(0, 1), 3), r.randint(0, 12)])
    wb.save(reg.p("Desktop/misc_data.xlsx"))
    reg.add("Desktop/misc_data.xlsx", "moderate", "Possibly original research data, but unlabeled; requires human review",
            lane="tabular", fmt="xlsx", title="Unlabeled numeric spreadsheet on desktop",
            summary="Header-less sheet of 30 rows: integer, a single letter b/y/w (plausibly bowl colour), a proportion and a count. Likely pilot pan-trap data but nothing in the file says so.",
            keywords=["unlabeled", "ambiguous", "spreadsheet"], difficulty="ambiguous")
    # big datalogger CSV (large-file handling)
    r = np.random.default_rng(7)
    rel = f"{LD}/dataloggers/HOBO_temp_rh_all_sites_2019-2021_6min.csv"
    path = reg.p(rel)
    n_per = 3 * 150 * 1440 // 6      # every 6 min, 3 seasons, 150 days
    with open(path, "w") as fh:
        fh.write("site,timestamp,temp_c,rh_pct,logger_id\n")
        base = np.datetime64("2019-05-01T00:00")
        for code, *_ in SITES:
            mins = np.arange(n_per) * 6
            ts = base + mins.astype("timedelta64[m]")
            tod = (mins % 1440) / 1440
            temp = 18 + 8 * np.sin(2 * np.pi * (tod - .3)) + r.normal(0, .6, n_per)
            rh = 70 - 20 * np.sin(2 * np.pi * (tod - .3)) + r.normal(0, 2, n_per)
            lines = [f"{code},{t},{a:.2f},{b:.1f},HOBO-{code}-01\n" for t, a, b in zip(ts.astype(str), temp, rh)]
            fh.writelines(lines)
    reg.add(rel, "high", "Original research data (microclimate loggers at survey sites)", lane="tabular",
            fmt="text/csv (large)", date="2021-10-15", title="Microclimate datalogger readings at all sites, 2019-2021",
            summary="Large CSV (~1.1 M rows) of temperature and relative humidity logged every 6 minutes at each survey site; tests streaming/downsampling of large tabular files.",
            keywords=["datalogger", "temperature", "humidity", "microclimate", "large file"], tags=["large_file"])
    reg.folder(f"{PBS}/data", "high", "Survey data: raw yearly specimen CSVs, quadrats, processed tables, site metadata and EML.")


def build_db_sci():
    sp = specimens()
    # SQLite
    rel = f"{PBS}/data/PBS_specimens.sqlite"
    p = reg.p(rel)
    if p.exists():
        p.unlink()
    con = sqlite3.connect(p)
    con.execute("create table sites(code text primary key, name text, county text, restored int, lat real, lon real, ownership text)")
    con.executemany("insert into sites values (?,?,?,?,?,?,?)", SITES)
    con.execute("create table specimens(" + ",".join(SPEC_HEADER) + ")")
    con.executemany(f"insert into specimens values ({','.join('?' * len(SPEC_HEADER))})", sp)
    con.execute("create table determiners(code text, name text)")
    con.executemany("insert into determiners values (?,?)", [("MA", "M. Achterberg"), ("PN", "P. Natarajan")])
    con.execute("create view v_affinis as select * from specimens where taxon='Bombus affinis'")
    con.commit(); con.close()
    reg.add(rel, "high", "Original research data: specimen database", lane="database", fmt="sqlite3",
            date="2023-01-15", title="Prairie Bee Survey specimen database (SQLite)",
            summary=f"SQLite database with sites (exact coordinates), {len(sp):,} specimens, determiners, and a view of rusty patched bumble bee records.",
            keywords=["SQLite", "specimen database", "Bombus affinis"], sens=("sensitive_location",))
    # HDF5 — datalogger summary arrays
    rel = f"{LD}/dataloggers/microclimate_daily.h5"
    with h5py.File(reg.p(rel), "w") as f:
        f.attrs["title"] = "Daily microclimate summaries, Prairie Bee Survey (SYNTHETIC)"
        f.attrs["units_temp"] = "degC"
        for code, *_ in SITES:
            g = f.create_group(code)
            g.create_dataset("tmax", data=np.round(np.random.default_rng(len(code)).normal(28, 3, 450), 2))
            g.create_dataset("tmin", data=np.round(np.random.default_rng(len(code) + 1).normal(14, 3, 450), 2))
            g.attrs["start"] = "2019-05-01"
    reg.add(rel, "high", "Original research data (derived microclimate arrays)", lane="scientific", fmt="hdf5",
            date="2021-11-01", title="Daily microclimate summaries per site (HDF5)",
            summary="HDF5 file with one group per site holding daily max/min temperature arrays (450 days) and unit attributes.",
            keywords=["HDF5", "microclimate", "temperature"], difficulty="subtle")
    # MATLAB
    rel = f"{LD}/quintero_models/occupancy_posteriors.mat"
    scipy.io.savemat(reg.p(rel), {"psi_mean": np.random.default_rng(3).uniform(.1, .9, (10, 28)),
                                  "sites": np.array([s[0] for s in SITES]), "taxa": np.array(BEE_TAXA, dtype=object),
                                  "note": "occupancy model posterior means, site x taxon (RQ 2021)"})
    reg.add(rel, "high", "Analysis outputs that produced the published results", lane="scientific", fmt="MATLAB v5 .mat",
            date="2021-02-11", title="Occupancy model posterior means (MATLAB)",
            summary="MATLAB file of site-by-taxon occupancy posterior means from Quintero's model, with site and taxon name arrays.",
            keywords=["MATLAB", "occupancy model", "posterior"], difficulty="subtle")
    # NumPy
    rel = f"{LD}/quintero_models/rarefaction_curves.npy"
    np.save(reg.p(rel), np.cumsum(np.random.default_rng(4).poisson(.6, (10, 200)), axis=1))
    reg.add(rel, "moderate", "Intermediate analysis array; meaning only clear from folder context", lane="scientific",
            fmt="numpy .npy", title="Rarefaction curve array (NumPy)",
            summary="10 x 200 integer array of cumulative species counts, consistent with rarefaction curves per site; no internal labels.",
            keywords=["NumPy", "rarefaction", "array"], difficulty="ambiguous")
    # Parquet
    rel = f"{PBS}/data/processed/specimens_2022.parquet"
    tbl = pa.Table.from_pylist([dict(zip(SPEC_HEADER, s)) for s in sp if s[2] == 2022])
    pq.write_table(tbl, reg.p(rel))
    reg.add(rel, "high", "Original research data (columnar copy of 2022 records)", lane="tabular", fmt="parquet",
            date="2023-01-15", title="2022 specimen records (Parquet)",
            summary="Parquet copy of the 2022 specimen records with typed columns; same rows as the 2022 CSV.",
            keywords=["Parquet", "specimen data", "2022"], sens=("sensitive_location",), tags=["same_content_different_format"],
            difficulty="subtle")
    # FASTA barcodes
    r = rng("fasta")
    seqs = []
    for i in range(40):
        s = [s for s in sp if s[9] == "Y"][i * 17]
        seq = "".join(r.choice("ACGT") for _ in range(658))
        seqs.append(f">{s[0]}|{s[7].replace(' ', '_')}|COI-5P|{s[1]}\n" + "\n".join(seq[j:j + 70] for j in range(0, 658, 70)))
    reg.p(f"{LD}/barcoding/COI_barcodes_batch07.fasta").write_text("\n".join(seqs) + "\n")
    reg.add(f"{LD}/barcoding/COI_barcodes_batch07.fasta", "high", "Specimen identification and DNA barcoding data",
            lane="scientific", fmt="FASTA", date="2021-03-02", title="COI DNA barcode sequences, batch 7",
            summary="FASTA file of 40 COI-5P barcode sequences (658 bp) labelled with specimen ID, taxon and site.",
            keywords=["DNA barcoding", "COI", "FASTA", "sequences"])
    reg.folder(LD, "high", "Copy of the lab external drive: dataloggers, model outputs, barcoding, GIS and raw photo dumps.")


def build_gis():
    G = f"{PBS}/GIS"
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [lo, la]},
              "properties": {"code": c, "name": n, "county": co, "restored": y, "ownership": ow}}
             for c, n, co, y, la, lo, ow in SITES]
    reg.p(f"{G}/survey_sites_EXACT.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, indent=1))
    reg.add(f"{G}/survey_sites_EXACT.geojson", "high", "GIS layers and maps of survey sites", lane="geospatial",
            fmt="GeoJSON", title="Survey site points with exact coordinates (GeoJSON)",
            summary="GeoJSON point layer of the ten survey sites with names, counties, restoration years and ownership; includes the exact location of the private remnant hosting an endangered bee.",
            keywords=["GIS", "GeoJSON", "survey sites", "coordinates"], sens=("sensitive_location",))
    pub = [f for f in feats if f["properties"]["code"] != "BRF"]
    reg.p(f"{G}/survey_sites_PUBLIC.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": pub}, indent=1))
    reg.add(f"{G}/survey_sites_PUBLIC.geojson", "high", "GIS layers of survey sites (public version)", lane="geospatial",
            fmt="GeoJSON", title="Survey site points, remnant withheld (public GeoJSON)",
            summary="Public version of the site layer with the private remnant removed, nine points.",
            keywords=["GIS", "GeoJSON", "public release"], tags=["near_duplicate_content"], difficulty="subtle")
    # shapefile set
    w = shapefile.Writer(str(reg.p(f"{G}/shp/pbs_sites")), shapeType=shapefile.POINT)
    for fld in ("code", "name", "county", "ownership"):
        w.field(fld, "C", size=40)
    w.field("restored", "N")
    for c, n, co, y, la, lo, ow in SITES:
        w.point(lo, la); w.record(c, n, co, ow, y)
    w.close()
    reg.p(f"{G}/shp/pbs_sites.prj").write_text(
        'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]')
    for ext, fmt in ((".shp", "ESRI shapefile geometry"), (".shx", "ESRI shapefile index"), (".dbf", "dBase attribute table"), (".prj", "WKT projection")):
        reg.add(f"{G}/shp/pbs_sites{ext}", "high", "GIS layers of survey sites (multi-file shapefile set)", lane="geospatial",
                fmt=fmt, title=f"Survey sites shapefile component ({ext})",
                summary=f"The {ext} member of a four-file ESRI shapefile of survey site points; should be described as one dataset with its siblings.",
                keywords=["shapefile", "GIS", ext], sens=("sensitive_location",), tags=["multi_file_dataset"], difficulty="subtle")
    # KML
    kml = "<?xml version='1.0' encoding='UTF-8'?>\n<kml xmlns='http://www.opengis.net/kml/2.2'><Document><name>PBS sites</name>" + "".join(
        f"<Placemark><name>{c} {n}</name><Point><coordinates>{lo},{la},0</coordinates></Point></Placemark>"
        for c, n, co, y, la, lo, ow in SITES if c != "BRF") + "</Document></kml>\n"
    reg.p(f"{G}/pbs_sites_for_google_earth.kml").write_text(kml)
    reg.add(f"{G}/pbs_sites_for_google_earth.kml", "high", "GIS layers of survey sites (Google Earth)", lane="geospatial", fmt="KML",
            title="Survey sites placemarks (KML)", summary="KML placemarks for nine public survey sites for Google Earth.",
            keywords=["KML", "Google Earth", "survey sites"], difficulty="subtle")
    # GPX track with BRF waypoint
    gpx = ("<?xml version='1.0'?><gpx version='1.1' creator='Garmin eTrex (synthetic)'><wpt lat='40.55262' lon='-88.01588'>"
           "<name>BRF-07</name><desc>B. affinis netted on Monarda</desc><time>2019-06-15T15:40:00Z</time></wpt>"
           "<trk><name>BRF transect 2019-06-15</name><trkseg>" +
           "".join(f"<trkpt lat='{40.5520 + i * 0.00004:.5f}' lon='{-88.0170 + i * 0.00006:.5f}'><time>2019-06-15T15:{i:02d}:00Z</time></trkpt>" for i in range(40)) +
           "</trkseg></trk></gpx>\n")
    reg.p(f"{LD}/gps/BRF_2019-06-15.gpx").write_text(gpx)
    reg.add(f"{LD}/gps/BRF_2019-06-15.gpx", "high", "Field GPS data for survey site (sensitive)", lane="geospatial", fmt="GPX",
            date="2019-06-15", title="GPS track and waypoint for rusty patched bumble bee observation",
            summary="Handheld GPS export with the waypoint BRF-07 marking the rusty patched bumble bee capture and the transect track walked at the Ritter remnant on 15 June 2019.",
            keywords=["GPS", "GPX", "waypoint", "Bombus affinis"], sens=("sensitive_location",))
    # Map images
    reg.p(f"{G}/maps/site_map_internal.png").write_bytes(charts.site_map())
    reg.add(f"{G}/maps/site_map_internal.png", "high", "Maps of survey sites", lane="image", fmt="png (map)",
            title="Internal survey site map including remnant", summary="Plotted map of all ten survey sites by latitude and longitude, private sites in red.",
            keywords=["map", "survey sites"], sens=("sensitive_location",))
    reg.p(f"{G}/maps/site_map_public.svg").write_bytes(charts.site_map(fmt="svg", exact_brf=False))
    reg.add(f"{G}/maps/site_map_public.svg", "high", "Maps of survey sites (public, vector)", lane="image", fmt="svg (vector map)",
            title="Public survey site map (SVG)", summary="Vector map of nine survey sites with the remnant withheld.",
            keywords=["map", "SVG", "vector"], tags=["vector_image"], difficulty="subtle")
    reg.folder(G, "high", "GIS: exact and public site layers in GeoJSON, a shapefile set, KML and maps.")


def build_code():
    A = f"{PBS}/analysis"
    R_code = """# gam_richness_v4.R  -- Rafael Quintero, April 2020
# Rarefied richness ~ s(age) + (1|site), offset log(bowl_days)
library(mgcv); library(dplyr)
d <- read.csv("../data/processed/richness_by_site_year.csv")
d$age_c <- pmin(d$years_since_restoration, 40)     # remnant coded as 40
m_all  <- gam(richness ~ s(age_c, k = 5) + s(site, bs = "re"), data = d, family = poisson)
m_spec <- gam(specialist_richness ~ s(age_c, k = 5) + s(site, bs = "re"), data = d, family = poisson)
m_noBRF <- update(m_spec, data = subset(d, site != "BRF"))   # Reviewer 1 sensitivity analysis
summary(m_all); summary(m_spec); summary(m_noBRF)
png("../figures/fig1_richness_age.png", 1200, 800, res = 200); plot(m_all, shade = TRUE); dev.off()
"""
    reg.p(f"{A}/gam_richness_v4.R").write_text(R_code)
    reg.add(f"{A}/gam_richness_v4.R", "high", "Analysis code that produced the published results", lane="code", fmt="R script",
            date="2020-04-22", title="R script fitting GAMs of bee richness against restoration age",
            summary="R script by Quintero fitting generalized additive mixed models for total and specialist richness with site random effects, a no-remnant sensitivity model, and writing Figure 1.",
            keywords=["R", "GAM", "mgcv", "analysis code"])
    rmd = "---\ntitle: 'Bare ground vs floral density'\nauthor: 'J. Feld'\n---\n\n```{r}\nq <- read.csv('../data/raw/floral_bareground_quadrats_2019-2022.csv')\n" \
          "summary(lm(pct_bare_ground ~ site, q))\n```\n\nBare ground beats flowers by dAIC 6.4.\n"
    reg.p(f"{A}/bareground_vs_floral.Rmd").write_text(rmd)
    reg.add(f"{A}/bareground_vs_floral.Rmd", "high", "Analysis notebooks that produced the published results", lane="code",
            fmt="R Markdown", date="2020-08-11", title="R Markdown comparing bare ground and floral density",
            summary="Feld's R Markdown analysis of quadrat data concluding that bare ground outperforms floral density (delta AIC 6.4).",
            keywords=["R Markdown", "bare ground", "model comparison"])
    py = '''"""clean_pantrap.py - merge yearly pan-trap CSVs, drop tipped bowls, compute bowl-days.
Author: Priya Natarajan, 2021."""
import glob
import pandas as pd

frames = [pd.read_csv(f) for f in sorted(glob.glob("../data/raw/pantrap_specimens_*.csv"))]
df = pd.concat(frames)
df = df[df.taxon != "Apis mellifera"]            # honey bees excluded from native richness
effort = df.groupby(["site", "year"]).station.nunique() * 15 * 4
print(effort.head())
df.to_csv("../data/processed/PBS_specimens_2016-2022_ALL.csv", index=False)
'''
    reg.p(f"{A}/clean_pantrap.py").write_text(py)
    reg.add(f"{A}/clean_pantrap.py", "high", "Analysis code/scripts", lane="code", fmt="Python script", date="2021-01-20",
            title="Python script merging and cleaning pan-trap data",
            summary="Natarajan's pandas script that merges yearly specimen CSVs, excludes honey bees from native richness, computes trapping effort and writes the compiled file.",
            keywords=["Python", "pandas", "data cleaning"])
    sql = ("-- queries used for the 2021 annual report\nSELECT site, COUNT(*) FROM specimens WHERE year=2020 GROUP BY site;\n"
           "SELECT COUNT(DISTINCT taxon) FROM specimens WHERE site='BRF';\nSELECT * FROM v_affinis ORDER BY date;\n")
    reg.p(f"{A}/report_queries.sql").write_text(sql)
    reg.add(f"{A}/report_queries.sql", "moderate", "Analysis scripts (short reporting queries)", lane="code", fmt="SQL",
            title="SQL queries for annual report counts", summary="Three SQL queries against the specimen database counting specimens by site, richness at the remnant, and listing rusty patched records.",
            keywords=["SQL", "queries", "reporting"], difficulty="subtle")
    # Jupyter notebook with outputs (image output embedded)
    nb = nbformat.v4.new_notebook()
    nb.cells = [nbformat.v4.new_markdown_cell("# Specialist lag figure\nRegenerates Fig. 2 for the JPE revision (with/without BRF)."),
                nbformat.v4.new_code_cell("import pandas as pd\nd = pd.read_csv('../data/processed/richness_by_site_year.csv')\nd.groupby('site').specialist_richness.mean()"),
                nbformat.v4.new_code_cell("plot_specialists(d, drop_brf=True)")]
    import base64
    nb.cells[2].outputs = [nbformat.v4.new_output("display_data", data={
        "image/png": base64.b64encode(charts.richness_vs_age(specialists=True, drop_brf=True)).decode(), "text/plain": "<Figure>"})]
    nb.cells[1].outputs = [nbformat.v4.new_output("execute_result", data={"text/plain": "site\nBRF 6.6\nSBP 5.0\nLAF 0.4"}, execution_count=1)]
    nbformat.write(nb, str(reg.p(f"{A}/specialist_lag_figS4.ipynb")))
    reg.add(f"{A}/specialist_lag_figS4.ipynb", "high", "Analysis notebooks and the figures they generated", lane="code",
            fmt="Jupyter notebook (with embedded PNG output)", date="2020-11-12",
            title="Notebook regenerating specialist-lag Figure S4", summary="Jupyter notebook that recomputes mean specialist richness per site and plots the specialist curve without the remnant for the revision's Figure S4; outputs embedded.",
            keywords=["Jupyter", "notebook", "figure S4", "revision"], tags=["notebook_with_outputs"])
    # Credentials file (must be flagged)
    reg.p(f"{A}/.env").write_text("# BOLD Systems API for barcode uploads\nBOLD_USER=machterberg\nBOLD_API_KEY=sk_test_SYNTHETIC_9f8a7b6c5d4e3f2a1b0c\n"
                                  "IDNR_PORTAL_PASSWORD=Prairie2019!synthetic\n")
    reg.add(f"{A}/.env", "none", "Credentials must be flagged and never published", lane="code", fmt="dotenv",
            title="Environment file with API key and portal password",
            summary="Hidden .env file containing a barcode database username, API key and a state portal password (synthetic values).",
            keywords=["credentials", "API key", "password"], sens=("credentials",), action="restrict_sensitive",
            tags=["hidden_file", "credentials"])
    # config yaml + log
    reg.p(f"{A}/config.yaml").write_text("data_dir: ../data\nyears: [2016, 2022]\nexclude_taxa: [Apis mellifera]\nk_smooth: 5\nremnant_age_code: 40\n")
    reg.add(f"{A}/config.yaml", "moderate", "Analysis configuration (parameters of published analysis)", lane="code", fmt="YAML",
            title="Analysis configuration YAML", summary="Parameters for the analysis scripts: data directory, years, excluded honey bees, smoothing basis and remnant age coding.",
            keywords=["YAML", "configuration"], difficulty="subtle")
    log = "".join(f"2021-01-20 14:{i:02d}:{(i * 7) % 60:02d} INFO merged pantrap_specimens_{2016 + i % 7}.csv rows={1200 + i * 13}\n" for i in range(60))
    reg.p(f"{A}/logs/clean_pantrap_2021-01-20.log").write_text(log + "2021-01-20 15:00:01 WARNING 37 tipped bowls coded as zero effort\n")
    reg.add(f"{A}/logs/clean_pantrap_2021-01-20.log", "low", "Run log of analysis script; little standalone value", lane="code", fmt="log text",
            title="Data cleaning run log", summary="Repetitive run log of the pan-trap cleaning script listing merged files and a warning about tipped bowls.",
            keywords=["log", "run output"], difficulty="ambiguous")
    # __pycache__ junk
    import py_compile
    py_compile.compile(str(reg.p(f"{A}/clean_pantrap.py")), cfile=str(reg.p(f"{A}/__pycache__/clean_pantrap.cpython-39.pyc")))
    reg.add(f"{A}/__pycache__/clean_pantrap.cpython-39.pyc", "none", "Application caches", lane="system", fmt="Python bytecode",
            title="Compiled Python bytecode cache", summary="Auto-generated .pyc cache of the cleaning script.",
            keywords=["cache", "bytecode"], action="exclude_system_file", tags=["system_file", "cache"])
    # figures folder
    F = f"{PBS}/figures"
    for name, data, t, s in [("fig1_richness_age.png", charts.richness_vs_age(dpi=200), "Figure 1: total richness vs restoration age", "Publication figure of total bee species richness against years since restoration with smoothed trend."),
                             ("fig2_specialists_age.png", charts.richness_vs_age(specialists=True, dpi=200), "Figure 2: specialist richness vs restoration age", "Publication figure of ground-nesting specialist richness rising across the chronosequence, remnant highest."),
                             ("figS4_specialists_noBRF.pdf", charts.richness_vs_age(fmt="pdf", specialists=True, drop_brf=True), "Figure S4: specialists without remnant (vector PDF)", "Vector PDF of the supplementary figure showing the specialist trend with the remnant site excluded."),
                             ("figS2_bowl_colour.png", charts.abundance_by_color(), "Figure S2: captures by bowl colour", "Line chart of specimens per year by pan-trap bowl colour; blue highest."),
                             ("taxa_top15.png", charts.taxa_bar(), "Top 15 taxa bar chart", "Horizontal bar chart of the 15 most abundant bee taxa across 2016-2022.")]:
        reg.p(f"{F}/{name}").write_bytes(data)
        reg.add(f"{F}/{name}", "high", "Figures generated by the analysis", lane="image" if name.endswith("png") else "document",
                fmt="png (chart)" if name.endswith("png") else "pdf (vector chart)", title=t, summary=s,
                keywords=["figure", "chart", "publication"], tags=["chart"])
    reg.folder(A, "high", "Analysis code: R, R Markdown, Python, SQL, Jupyter, config, logs, a credentials file and a bytecode cache.")
    reg.folder(F, "high", "Publication figures generated by the analysis.")


def run():
    build_tabular(); build_db_sci(); build_gis(); build_code()
    reg.folder(PBS, "high", "The Prairie Bee Survey: data, analysis code, figures, GIS, field notebooks, photographs and lab drive copy.")
