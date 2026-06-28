"""Local dev tool — scrape SSYK 2012 descriptions + synonym titles from SCB's
SSYK-Sök site and write ssyk_descriptions.json (shipped in the repo, read at
runtime by the app). NOT used by the deployed container.

The site is server-rendered HTML at https://ssyksok.scb.se/SsykSok/SSYK2012/{code}.
We scrape, per code, the Swedish name, the description text, and (for 4-digit
codes) the list of "benämningar" (alternative job titles / synonyms).

The 1→2→3→4-digit hierarchy is derived from the 4-digit codes in
occupations_cache.json, so we only fetch each code's page once.

Run:  python build_ssyk_descriptions.py
Re-run only when SCB updates the classification (rare). Be polite — there's a
small delay between requests.
"""
import json
import os
import time
import requests
from bs4 import BeautifulSoup

HERE       = os.path.dirname(os.path.abspath(__file__))
OCC_CACHE  = os.path.join(HERE, "occupations_cache.json")
OUT_FILE   = os.path.join(HERE, "ssyk_descriptions.json")
BASE       = "https://ssyksok.scb.se/SsykSok/SSYK2012/{code}"
HEADERS    = {"User-Agent": "SCB-Salary-Explorer/1.0 (personal data tool; contact qvist.kristoffer@gmail.com)"}
DELAY_SEC  = 0.25


def all_codes() -> list[str]:
    """Every SSYK node (1–4 digit) derived from the 4-digit occupation codes."""
    with open(OCC_CACHE, encoding="utf-8") as f:
        occ = json.load(f)
    four = [c for c in occ.get("SV", {}) if c != "0000" and len(c) == 4 and c.isdigit()]
    nodes = set()
    for c in four:
        for n in (1, 2, 3, 4):
            nodes.add(c[:n])
    # sort by length then value so parents come before children
    return sorted(nodes, key=lambda c: (len(c), c))


def parse_page(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    out  = {"name_sv": "", "desc": "", "synonyms": []}

    h2 = soup.find("h2", id="desc-heading")
    if h2:
        strong = h2.find("strong")
        code   = strong.get_text(strip=True) if strong else ""
        full   = h2.get_text(" ", strip=True)
        out["name_sv"] = full[len(code):].strip() if code else full

    sec = soup.find("section", attrs={"aria-label": "Beskrivning av vald kod"})
    if sec:
        body  = sec.find(class_="card-body") or sec
        parts = []
        for el in body.find_all(["p", "li"]):
            txt = el.get_text(" ", strip=True)
            if not txt or txt.rstrip(":").lower() == "beskrivning":
                continue
            parts.append(txt)
        out["desc"] = "\n".join(parts)

    for tbl in soup.find_all("table", class_="ssyk-table"):
        if tbl.get("aria-label", "").startswith("Lista med benämningar"):
            for tr in tbl.select("tbody tr"):
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    span = tds[1].find("span")
                    name = (span.get_text(strip=True) if span
                            else tds[1].get_text(strip=True))
                    if name:
                        out["synonyms"].append(name)
            break
    return out


def main():
    codes = all_codes()
    print(f"{len(codes)} SSYK nodes to fetch")
    sess  = requests.Session()
    sess.headers.update(HEADERS)
    nodes = {}
    for i, code in enumerate(codes, 1):
        try:
            r = sess.get(BASE.format(code=code), timeout=30)
            r.raise_for_status()
            data = parse_page(r.text)
        except Exception as e:
            print(f"  ! {code}: {e}")
            data = {"name_sv": "", "desc": "", "synonyms": []}
        # children derived from the code set
        data["children"] = [c for c in codes
                            if len(c) == len(code) + 1 and c.startswith(code)]
        nodes[code] = data
        if i % 25 == 0 or i == len(codes):
            print(f"  {i}/{len(codes)}  (last: {code} – {data['name_sv'][:40]})")
        time.sleep(DELAY_SEC)

    payload = {
        "built_at": time.strftime("%Y-%m-%d %H:%M"),
        "source":   "https://ssyksok.scb.se/SsykSok/SSYK2012/",
        "nodes":    nodes,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    n_syn = sum(len(v["synonyms"]) for v in nodes.values())
    print(f"Wrote {OUT_FILE}: {len(nodes)} nodes, {n_syn} synonym titles")


if __name__ == "__main__":
    main()
