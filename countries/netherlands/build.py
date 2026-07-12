"""Occupation labels + code map for the Netherlands (CBS table 85517NED).

CBS's OData occupation dimension ('Beroep') uses OPAQUE keys (A000164) whose
Title carries the BRC-2014 numeric code + Dutch name ("0112 Docenten
beroepsgerichte vakken"). The framework wants the numeric code (so its
prefix-hierarchy drill-down works), so we split each title into
  numeric_code (01 / 011 / 0111)  +  name
and keep a keymap {numeric_code: opaque CBS key} for querying.

The Title's Dutch name is TRUNCATED at 40 chars by CBS ("Docenten hoger
onderwijs en hoog…"); the full Dutch name is the text before the first colon in
the entry's Description field, so we read the name from there instead.

CBS publishes NO English occupation names for this table, so we ship our own
English translations of the BRC-2014 groups (_EN below). Any code missing from
_EN falls back to its Dutch name.
"""
from __future__ import annotations

import datetime
import json
import os
import time

import requests

BASE = "https://opendata.cbs.nl/ODataApi/odata/85517NED/"
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "netherlands_labels.json")
_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")
DEFAULT_LATEST_YEAR = 2024

# --- English translations of the BRC-2014 occupation groups ------------------
# CBS publishes no English names for 85517NED, so these are our own translations
# of the official Dutch group names (levels 2–4 digit). Codes absent here fall
# back to the Dutch name.
_EN = {
    "01": "Educational occupations",
    "011": "Teachers",
    "0111": "Higher-education teachers and professors",
    "0112": "Vocational-subject teachers, secondary education",
    "0113": "General-subject teachers, secondary education",
    "0114": "Primary-school teachers",
    "0115": "Education specialists and other teachers",
    "012": "Sports instructors",
    "0121": "Sports instructors",
    "013": "Childcare workers and teaching assistants",
    "0131": "Childcare workers and teaching assistants",
    "02": "Creative and linguistic occupations",
    "021": "Authors and artists",
    "0211": "Librarians and curators",
    "0212": "Authors and linguists",
    "0213": "Journalists",
    "0214": "Visual artists",
    "0215": "Performing artists",
    "022": "Artistic and cultural specialists",
    "0221": "Graphic and product designers",
    "0222": "Photographers and interior designers",
    "03": "Commercial occupations",
    "031": "Marketing, PR and sales advisers",
    "0311": "Marketing, PR and sales advisers",
    "032": "Sales representatives and buyers",
    "0321": "Sales representatives and buyers",
    "033": "Salespersons",
    "0331": "Shopkeepers and retail team leaders",
    "0332": "Retail sales assistants",
    "0333": "Cashiers",
    "0334": "Outbound call-centre and other salespersons",
    "04": "Business-economic and administrative occupations",
    "041": "Business-management and administration specialists",
    "0411": "Accountants",
    "0412": "Financial specialists and economists",
    "0413": "Business analysts and management consultants",
    "0414": "Policy advisers",
    "0415": "HR and career-development specialists",
    "042": "Business and administration associate professionals",
    "0421": "Bookkeepers",
    "0422": "Business-service agents",
    "0423": "Executive secretaries",
    "043": "Administrative staff",
    "0431": "Administrative clerks",
    "0432": "Secretaries",
    "0433": "Receptionists and telephonists",
    "0434": "Accounting clerks",
    "0435": "Transport planners and logistics clerks",
    "05": "Managers",
    "051": "General directors",
    "0511": "General directors",
    "052": "Administrative and commercial managers",
    "0521": "Business and administration services managers",
    "0522": "Sales and marketing managers",
    "053": "Production and specialised-services managers",
    "0531": "Production managers",
    "0532": "Logistics managers",
    "0533": "ICT managers",
    "0534": "Healthcare-institution managers",
    "0535": "Education managers",
    "0536": "Specialised-services managers",
    "054": "Hospitality, retail and other-services managers",
    "0541": "Hospitality managers",
    "0542": "Retail and wholesale managers",
    "0543": "Commercial and personal-services managers",
    "055": "Managers n.e.c.",
    "0551": "Managers n.e.c.",
    "06": "Public administration, security and legal occupations",
    "061": "Government officials and administrators",
    "0611": "Government administrators",
    "0612": "Government officials",
    "062": "Legal professionals",
    "0621": "Legal professionals",
    "063": "Security workers",
    "0631": "Police inspectors",
    "0632": "Police and fire service",
    "0633": "Security guards",
    "0634": "Military occupations",
    "07": "Technical occupations",
    "071": "Engineers and researchers in science and engineering",
    "0711": "Biologists and natural scientists",
    "0712": "Engineers (except electrical)",
    "0713": "Electrical engineers",
    "0714": "Architects",
    "072": "Science and engineering associate professionals",
    "0721": "Civil-engineering and science technicians",
    "0722": "Production supervisors, industry and construction",
    "0723": "Process operators",
    "073": "Construction workers",
    "0731": "Structural construction workers",
    "0732": "Carpenters",
    "0733": "Finishing construction workers",
    "0734": "Plumbers and pipe fitters",
    "0735": "Painters and metal sprayers",
    "074": "Metalworkers and machine fitters",
    "0741": "Metalworkers and structural workers",
    "0742": "Welders and sheet-metal workers",
    "0743": "Car mechanics",
    "0744": "Machine fitters",
    "075": "Food-processing and other craft trades",
    "0751": "Butchers",
    "0752": "Bakers",
    "0753": "Product inspectors",
    "0754": "Furniture makers, tailors and upholsterers",
    "0755": "Printing and handicraft workers",
    "076": "Electricians and electronics fitters",
    "0761": "Electricians and electronics fitters",
    "077": "Machine operators and assemblers",
    "0771": "Machine operators",
    "0772": "Assemblers",
    "078": "Labourers in construction and industry",
    "0781": "Labourers in construction and industry",
    "08": "ICT occupations",
    "081": "ICT specialists",
    "0811": "Software and application developers",
    "0812": "Database and network specialists",
    "082": "ICT associate professionals",
    "0821": "ICT user support",
    "0822": "Radio and television technicians",
    "09": "Agricultural occupations",
    "091": "Gardeners, crop and livestock farmers",
    "0911": "Farmers and foresters",
    "0912": "Landscapers, gardeners and growers",
    "0913": "Livestock farmers",
    "092": "Agricultural labourers",
    "0921": "Agricultural labourers",
    "10": "Healthcare and welfare occupations",
    "101": "Doctors, therapists and specialist nurses",
    "1011": "Doctors",
    "1012": "Specialist nurses",
    "1013": "Physiotherapists",
    "102": "Social-science specialists",
    "1021": "Social workers",
    "1022": "Psychologists and sociologists",
    "103": "Healthcare associate professionals",
    "1031": "Laboratory technicians",
    "1032": "Pharmacy assistants",
    "1033": "Nurses (vocational)",
    "1034": "Medical practice assistants",
    "1035": "Medical associate professionals",
    "104": "Social and residential-care workers",
    "1041": "Social and residential-care workers",
    "105": "Care workers",
    "1051": "Care workers",
    "11": "Service occupations",
    "111": "Personal-service workers",
    "1111": "Travel attendants and guides",
    "1112": "Cooks",
    "1113": "Waiters and bar staff",
    "1114": "Hairdressers and beauticians",
    "1115": "Caretakers and cleaning supervisors",
    "1116": "Other personal-service providers",
    "112": "Cleaners and kitchen helpers",
    "1121": "Cleaners",
    "1122": "Kitchen helpers",
    "12": "Transport and logistics occupations",
    "121": "Vehicle drivers and mobile-machine operators",
    "1211": "Ship's deck officers and pilots",
    "1212": "Car, taxi and van drivers",
    "1213": "Bus and tram drivers",
    "1214": "Truck drivers",
    "1215": "Mobile-machine operators",
    "122": "Transport and logistics labourers",
    "1221": "Loaders, unloaders and shelf fillers",
    "1222": "Refuse collectors and newspaper deliverers",
    "13": "Other occupational class",
    "131": "Other occupational segment",
    "1311": "Other occupational group",
}


def latest_year() -> int:
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("netherlands_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def save_latest_year(year: int):
    data = {}
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["netherlands_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get(path, tries=6):
    last = None
    for _ in range(tries):
        r = requests.get(BASE + path, timeout=120)
        if r.status_code == 200:
            return r.json()["value"]
        last = f"HTTP {r.status_code}"
        time.sleep(4)
    raise RuntimeError(f"CBS metadata unavailable ({path}): {last}")


def available_years() -> list[int]:
    per = _get("Perioden")
    return sorted(int(p["Key"][:4]) for p in per if p["Key"][:4].isdigit())


def _parse() -> tuple[dict, dict]:
    """→ (codes {numeric: dutch_name}, keymap {numeric: cbs_key}).

    The numeric code comes from the Title prefix; the Dutch name comes from the
    Description (text before the first ':') because the Title's name is
    truncated at 40 chars by CBS. Falls back to the (truncated) Title name if a
    Description is missing.
    """
    codes, keymap = {}, {}
    for v in _get("Beroep"):
        key, title = v["Key"], (v.get("Title") or "").strip()
        parts = title.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit() and 1 <= len(parts[0]) <= 4:
            desc = (v.get("Description") or "").strip()
            name = desc.split(":", 1)[0].strip() if ":" in desc else parts[1]
            codes[parts[0]] = name
            keymap[parts[0]] = key
    return codes, keymap


def build(out_path: str = OUT, log=print) -> dict:
    log("fetching BRC occupation labels from CBS (85517NED) …")
    codes, keymap = _parse()
    codes_en = {c: _EN.get(c, name) for c, name in codes.items()}  # English, Dutch fallback
    missing = [c for c in codes if c not in _EN]
    if missing:
        log(f"  note: {len(missing)} codes without an English translation (Dutch kept): {missing}")
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": BASE,
        "classification": "BRC 2014 (Beroepenindeling ROA-CBS); levels 2–4 digit",
        "codes": {"EN": codes_en, "NL": codes},   # EN = our translations, NL = full Dutch
        "keymap": keymap,
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)
    leaves = sum(1 for c in codes if len(c) == 4)
    log(f"wrote {len(codes)} BRC codes ({leaves} leaf)")
    return {"built_at": payload["built_at"], "codes": len(codes), "leaves": leaves}
