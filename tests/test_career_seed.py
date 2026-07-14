"""Integrity tests for the curated Career Paths seed (cp_* register).

Integration test: reads the live register via careerpaths (needs Supabase creds).
Skips cleanly (exit 0) if the register is unreachable/empty, so it never blocks a
CI run without credentials. Asserts referential + semantic integrity of the seed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import careerpaths as cp  # noqa: E402


def main() -> int:
    titles, terr = cp.titles()
    rels, rerr = cp.relationships()
    if terr or rerr or not titles:
        print("SKIP — register unreachable or empty (no creds / not seeded)")
        return 0

    by = {t["title_id"]: t for t in titles}
    fails: list[str] = []

    for t in titles:
        lo, mid, hi = float(t["lo_pct"]), float(t["mid_pct"]), float(t["hi_pct"])
        if not (0 <= lo <= mid <= hi <= 100):
            fails.append(f"band order {t['title_id']}: {lo}/{mid}/{hi}")
        if t["track"] not in ("ic", "specialist", "management"):
            fails.append(f"bad track {t['title_id']}: {t['track']}")
        if t["confidence"] not in ("strong", "moderate", "limited", "experimental"):
            fails.append(f"bad confidence {t['title_id']}")
        if not str(t["primary_ssyk"]).isdigit() or len(str(t["primary_ssyk"])) != 4:
            fails.append(f"bad SSYK {t['title_id']}: {t['primary_ssyk']}")

    for r in rels:
        if r["from_title"] not in by:
            fails.append(f"rel {r['rel_id']} unknown from_title {r['from_title']}")
        if r["to_title"] not in by:
            fails.append(f"rel {r['rel_id']} unknown to_title {r['to_title']}")
        if r["from_title"] in by and r["to_title"] in by:
            same = str(by[r["from_title"]]["primary_ssyk"]) == str(by[r["to_title"]]["primary_ssyk"])
            if bool(r["same_ssyk"]) != same:
                fails.append(f"rel {r['rel_id']} same_ssyk={r['same_ssyk']} but SSYK-equal={same}")
        if r["rel_type"] not in ("progression", "leadership", "specialist", "lateral", "entry", "related"):
            fails.append(f"rel {r['rel_id']} bad type {r['rel_type']}")

    for fam in {t["family_id"] for t in titles}:
        if not any(t["published"] for t in titles if t["family_id"] == fam):
            fails.append(f"family {fam} has no published title")

    for x in fails:
        print("FAIL", x)
    print(f"\n{len(titles)} titles · {len(rels)} relationships · {len(fails)} issue(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
