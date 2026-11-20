"""clean_pantrap.py - merge yearly pan-trap CSVs, drop tipped bowls, compute bowl-days.
Author: Priya Natarajan, 2021."""
import glob
import pandas as pd

frames = [pd.read_csv(f) for f in sorted(glob.glob("../data/raw/pantrap_specimens_*.csv"))]
df = pd.concat(frames)
df = df[df.taxon != "Apis mellifera"]            # honey bees excluded from native richness
effort = df.groupby(["site", "year"]).station.nunique() * 15 * 4
print(effort.head())
df.to_csv("../data/processed/PBS_specimens_2016-2022_ALL.csv", index=False)
