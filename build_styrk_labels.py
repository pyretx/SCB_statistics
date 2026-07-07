"""Build styrk_labels.json — STYRK-08 occupation codes → names, bilingual + all
levels (CLI shim).

The actual build logic now lives in countries/norway/build.py (a SHIPPED module,
so the admin panel can trigger a rebuild at runtime). This file is just the
offline CLI entry point; it stays dockerignored.

Source: the SSB Statbank table 11418 'Yrke' variable metadata, fetched in both
English (/en/) and Norwegian (/no/), every numeric level 1–4 digit. This one
file feeds the occupation menu, the drill-down, the language toggle and the
code browser without touching SSB at runtime.

    python build_styrk_labels.py
"""
from countries.norway.build import build

if __name__ == "__main__":
    build(log=print)
