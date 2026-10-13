"""Compatibility path for the live pipeline's workbench.schema imports.

The repository stores the shared schema in src/schema. Both import spellings
resolve source there, without copying a second schema definition.
"""
from pathlib import Path

__path__ = [str(Path(__file__).resolve().parents[2] / "schema")]
