"""Dev tool: build pcs_labels.json (PCS-ESE 2017 code → French label).

Downloads INSEE's official list (486 professions + categories + groups) and
writes a JSON used by the France page for occupation names. Run locally when
the nomenclature changes (rare); the JSON is committed to the repo.
English labels can be added later (see build_ssyk_translations.py pattern):
schema is {code: {"fr": str, "en": str|None}}.

Usage:  python build_pcs_labels.py        (needs: pip install xlrd)
"""
import io
import json
import re
import datetime

import pandas as pd
import requests

URL  = "https://www.insee.fr/fr/statistiques/fichier/2912545/PCS-ESE_2017_Liste.xls"
DEST = "pcs_labels.json"

print(f"downloading {URL} …")
r = requests.get(URL, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
r.raise_for_status()

sheets = pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None, dtype=str)
print("sheets:", {k: v.shape for k, v in sheets.items()})

# Collect every (code, label) pair found anywhere: 1-digit groups, 2-digit
# categories (CS), and 4-char detailed professions. The file uses lowercase
# letters ("233a") while Melodi serves uppercase ("233A") — normalize to upper.
code_re = re.compile(r"^(\d[\dA-Za-z]{0,3})$")
labels: dict[str, dict] = {}
for name, df in sheets.items():
    for _, row in df.iterrows():
        vals = [str(v).strip() for v in row.tolist() if str(v).strip() not in ("", "nan")]
        if len(vals) < 2:
            continue
        code, label = vals[0], vals[-1]
        if code_re.match(code) and len(label) > 3 and not code_re.match(label):
            labels.setdefault(code.upper(), {"fr": label, "en": None})

by_len = {}
for c in labels:
    by_len.setdefault(len(c), []).append(c)
print("codes by length:", {k: len(v) for k, v in sorted(by_len.items())})
for sample in ("3", "38", "233A", "480B"):
    print(f"  {sample}: {labels.get(sample, {}).get('fr', '—')}")

with open(DEST, "w", encoding="utf-8") as f:
    json.dump({"built_at": datetime.date.today().isoformat(),
               "source": URL, "labels": labels}, f, ensure_ascii=False, indent=1)
print(f"wrote {DEST}: {len(labels)} codes")
