"""Japan — e-Stat API, Basic Survey on Wage Structure (賃金構造基本統計調査).

Open e-Stat API (needs a free app_id in secrets [estat] app_id). Table 0003426315
(一般_職種（小分類）DB) gives 所定内給与額 (scheduled monthly cash earnings) by the
DETAILED occupation classification (JSCO 2020 small groups, 144 occupations) × sex,
national, 2020–2023 (→ a trend). e-Stat serves the value in 千円 → ×1000 = yen/mo.
The 144 detailed codes map by range to the 11 JSCO major groups, so we build a
2-level hierarchy (major → detailed) with prefix-nestable framework codes
(major "MM" + within-major "NN"). Occupation names are Japanese-only in e-Stat, so
EN titles are supplied here; JA native names come from the API.
"""
from __future__ import annotations

import datetime
import gzip
import json
import os

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "japan_earnings.json.gz")
_B = "https://api.e-stat.go.jp/rest/3.0/app/json"
TID = "0003426315"          # 一般_職種（小分類）DB
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}
STAT_COLS = ["mean"]
_TAB = "42"                 # 所定内給与額 (scheduled monthly cash earnings)
_SIZE = "01"               # 企業規模計（10人以上）
_SEX = {"01": "total", "02": "men", "03": "women"}

# 11 JSCO-2020 major groups (framework code "01"–"11") — EN + JA.
_MAJOR_EN = {
    "01": "Managers", "02": "Professionals and engineers", "03": "Clerical workers",
    "04": "Sales workers", "05": "Service workers",
    "06": "Security and protective service workers",
    "07": "Agriculture, forestry and fishery workers",
    "08": "Manufacturing process workers",
    "09": "Transport and machine operation workers",
    "10": "Construction and mining workers",
    "11": "Carrying, cleaning, packaging and related workers",
}
_MAJOR_JA = {
    "01": "管理的職業従事者", "02": "専門的・技術的職業従事者", "03": "事務従事者",
    "04": "販売従事者", "05": "サービス職業従事者", "06": "保安職業従事者",
    "07": "農林漁業従事者", "08": "生産工程従事者", "09": "輸送・機械運転従事者",
    "10": "建設・採掘従事者", "11": "運搬・清掃・包装等従事者",
}


def _major_of(jsco: str) -> str | None:
    """JSCO detailed code (4-digit str) → major framework code, by code range."""
    try:
        n = int(jsco)
    except ValueError:
        return None
    if n == 1031:
        return "01"
    if 1051 <= n <= 1249:
        return "02"
    if 1251 <= n <= 1311:
        return "03"
    if 1321 <= n <= 1349:
        return "04"
    if 1361 <= n <= 1421:
        return "05"
    if 1453 <= n <= 1459:
        return "06"
    if n == 1461:
        return "07"
    if 1491 <= n <= 1592:
        return "08"
    if 1601 <= n <= 1649:
        return "09"
    if 1651 <= n <= 1691:
        return "10"
    if 1702 <= n <= 1739:
        return "11"
    return None


# JSCO-2020 detailed code → English name (144 occupations).
_EN = {
    "1031": "Managers", "1051": "Researchers",
    "1072": "Electrical, electronic & telecom engineers (excl. network)",
    "1073": "Mechanical engineers", "1074": "Transport-equipment engineers",
    "1076": "Metals engineers", "1077": "Chemical engineers",
    "1091": "Architects & building engineers", "1092": "Civil engineers",
    "1093": "Surveying engineers", "1101": "Systems consultants & designers",
    "1104": "Software developers", "1109": "Other IT & communications engineers",
    "1119": "Engineers n.e.c.", "1121": "Physicians", "1122": "Dentists",
    "1123": "Veterinarians", "1124": "Pharmacists", "1131": "Public health nurses",
    "1132": "Midwives", "1133": "Registered nurses", "1134": "Assistant nurses",
    "1141": "Radiological technologists", "1143": "Clinical laboratory technicians",
    "1144": "Physical/occupational/speech/orthoptic therapists",
    "1146": "Dental hygienists", "1147": "Dental technicians", "1151": "Dietitians",
    "1159": "Other health professionals", "1163": "Nursery & childcare workers",
    "1168": "Care managers", "1169": "Other social-welfare professionals",
    "1173": "Legal professionals", "1181": "Certified & tax accountants",
    "1189": "Other business, finance & insurance professionals",
    "1191": "Kindergarten teachers", "1192": "Elementary & junior-high teachers",
    "1194": "High-school teachers", "1196": "University professors",
    "1197": "University associate professors",
    "1198": "University lecturers & assistant professors", "1199": "Other teachers",
    "1201": "Religious workers", "1211": "Writers, journalists & editors",
    "1221": "Artists, photographers & videographers", "1224": "Designers",
    "1231": "Musicians & stage performers", "1244": "Private tutors & instructors",
    "1249": "Professionals n.e.c.", "1251": "General-affairs & HR clerks",
    "1253": "Planning clerks", "1254": "Reception & information clerks",
    "1255": "Secretaries", "1256": "Telephone-service clerks",
    "1257": "General office clerks", "1259": "Other general clerical workers",
    "1261": "Accounting clerks", "1271": "Production-related clerks",
    "1281": "Sales & marketing clerks", "1291": "Field/outdoor clerks",
    "1301": "Transport & postal clerks", "1311": "Office-machine operators",
    "1321": "Shop sales clerks", "1324": "Other retail sales workers",
    "1331": "Sales-related workers", "1344": "Automobile sales workers",
    "1345": "Machinery/telecom/systems sales workers (excl. autos)",
    "1346": "Financial sales workers", "1347": "Insurance sales workers",
    "1349": "Other sales workers", "1361": "Care workers (medical/welfare)",
    "1362": "Home-visit care workers", "1371": "Nursing aides",
    "1379": "Other health & medical service workers", "1381": "Barbers & beauticians",
    "1383": "Beauty & bath service workers (excl. beauticians)",
    "1385": "Cleaning & laundry workers", "1391": "Cooks & food-preparation workers",
    "1403": "Food & beverage serving workers", "1404": "Flight attendants",
    "1405": "Personal-care attendants", "1406": "Amusement-facility attendants",
    "1411": "Building & facility caretakers", "1421": "Other service workers",
    "1453": "Security guards", "1459": "Other protective-service workers",
    "1461": "Agriculture, forestry & fishery workers",
    "1491": "Iron, steel & non-ferrous metal smelting workers",
    "1492": "Casting & forging workers", "1493": "Metal machine-tool operators",
    "1494": "Metal-press workers", "1495": "Ironworkers & platers",
    "1496": "Sheet-metal workers", "1497": "Metal engraving & surface-treatment workers",
    "1498": "Metal welding & cutting workers",
    "1499": "Other metal-product manufacturing workers",
    "1501": "Chemical-product manufacturing workers",
    "1502": "Ceramics & stone-product manufacturing workers",
    "1503": "Food, beverage & tobacco manufacturing workers",
    "1505": "Textile, apparel & fibre-product manufacturing workers",
    "1506": "Wood & paper-product manufacturing workers",
    "1507": "Printing & bookbinding workers",
    "1508": "Rubber & plastic-product manufacturing workers",
    "1509": "Other product manufacturing workers (excl. metal)",
    "1511": "General/production/industrial machinery assemblers",
    "1512": "Electrical-machinery assemblers", "1513": "Automobile assemblers",
    "1514": "Other machinery assemblers",
    "1551": "Machinery & electrical-equipment maintenance & repair workers",
    "1553": "Automobile maintenance & repair workers",
    "1554": "Other machinery maintenance & repair workers",
    "1561": "Product inspectors (metal products)",
    "1571": "Product inspectors (excl. metal)", "1581": "Machinery inspectors",
    "1591": "Painters & sign makers",
    "1592": "Drafting & other production-related workers",
    "1601": "Railway operators", "1611": "Bus drivers", "1612": "Taxi drivers",
    "1613": "Passenger-car drivers (excl. taxi)",
    "1614": "Commercial heavy-truck drivers",
    "1615": "Commercial truck drivers (excl. heavy)", "1616": "Private truck drivers",
    "1619": "Other motor-vehicle drivers", "1624": "Aircraft pilots",
    "1631": "Train conductors", "1639": "Transport workers n.e.c.",
    "1641": "Power-plant & substation operators", "1643": "Crane & winch operators",
    "1645": "Construction & well-drilling machine operators",
    "1649": "Other stationary & construction machine operators",
    "1651": "Building-frame construction workers", "1661": "Carpenters",
    "1666": "Plumbers & pipe fitters", "1669": "Other construction workers",
    "1671": "Electrical construction workers",
    "1681": "Civil-engineering & railway-track workers",
    "1691": "Dam/tunnel excavation & mining workers",
    "1702": "Ship & dock cargo handlers", "1703": "Other carrying workers",
    "1711": "Building cleaners",
    "1712": "Cleaners (excl. buildings) & waste-disposal workers",
    "1721": "Packaging workers",
    "1739": "Carrying, cleaning & packaging workers n.e.c.",
}


def _app_id() -> str:
    try:
        import streamlit as st
        v = (st.secrets.get("estat") or {}).get("app_id")
        if v:
            return v
    except Exception:
        pass
    import tomllib
    for p in (os.path.join(_ROOT, ".streamlit", "secrets.toml"), "/root/scb-secrets.toml"):
        try:
            with open(p, "rb") as f:
                v = (tomllib.load(f).get("estat") or {}).get("app_id")
            if v:
                return v
        except Exception:
            continue
    return os.environ.get("ESTAT_APP_ID", "")


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("japan_latest_year", 2023))
    except Exception:
        return 2023


def build(out_path: str = OUT, log=print) -> dict:
    app = _app_id()
    if not app:
        raise RuntimeError("e-Stat app_id missing ([estat] app_id in secrets)")
    # native JA names from the classification metadata
    m = requests.get(f"{_B}/getMetaInfo", params={"appId": app, "statsDataId": TID},
                     headers=_UA, timeout=90, verify=False).json()
    ja_name = {}
    for cls in m.get("GET_META_INFO", {}).get("METADATA_INF", {}).get("CLASS_INF", {}).get("CLASS_OBJ", []):
        if cls.get("@id") == "cat03":
            for o in (cls.get("CLASS") or []):
                ja_name[o.get("@code")] = o.get("@name")

    # framework leaf code per JSCO code: major "MM" + within-major sequence "NN"
    leaves = sorted(c for c in _EN if _major_of(c))
    seq: dict = {}
    fw: dict = {}
    for c in leaves:
        mj = _major_of(c)
        seq[mj] = seq.get(mj, 0) + 1
        fw[c] = f"{mj}{seq[mj]:02d}"

    d = requests.get(f"{_B}/getStatsData", params={
        "appId": app, "statsDataId": TID, "cdTab": _TAB, "cdCat01": _SIZE},
        headers=_UA, timeout=120, verify=False).json()
    vals = d.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {}).get("DATA_INF", {}).get("VALUE", [])

    stats: dict = {}
    for v in vals:
        js = v.get("@cat03")
        sx = _SEX.get(v.get("@cat02"))
        if js not in fw or not sx:
            continue
        try:
            yen = int(round(float(v.get("$")) * 1000))
        except (TypeError, ValueError):
            continue
        yr = str(int(v.get("@time", "0")[:4]))
        (stats.setdefault(yr, {}).setdefault(sx, {})[fw[js]]) = [yen]

    # codes: majors (navigation nodes) + leaves
    codes_en = dict(_MAJOR_EN)
    codes_ja = dict(_MAJOR_JA)
    for c in leaves:
        codes_en[fw[c]] = _EN[c]
        codes_ja[fw[c]] = ja_name.get(c, _EN[c])

    years = sorted(int(y) for y in stats)
    latest = max(years) if years else latest_year()
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": "https://www.e-stat.go.jp/dbview?sid=0003426315",
        "source_name": "e-Stat — Basic Survey on Wage Structure (賃金構造基本統計調査), MHLW",
        "classification": "JSCO 2020 occupations (major + detailed; e-Stat 0003426315)",
        "note": "Mean scheduled monthly cash earnings (JPY) by detailed occupation "
                "(JSCO major → small group) × sex, enterprises with 10+ employees.",
        "years": years, "year": latest, "currency": "JPY",
        "stat_cols": STAT_COLS, "sexes": ["total", "women", "men"],
        "codes": {"EN": codes_en, "JA": codes_ja}, "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes_en)} codes ({len(leaves)} detailed occupations under "
        f"11 majors), {len(years)} years ({size/1e6:.3f} MB)")
    return {"built_at": payload["built_at"], "year": latest, "years": years,
            "codes": len(codes_en), "leaves": len(leaves), "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "years": d.get("years"), "size": os.path.getsize(path),
                "source": d.get("source")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
