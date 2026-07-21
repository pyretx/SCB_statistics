"""Backfill seniority-anchored percentile bands for pipeline-created career
titles (title_id like ``NNNN-N``), replacing the flat 25/45/62 placeholder.

The band logic lives in ``careerpaths_v1.calibrate_band`` (shared with the admin
approval path, so new titles get the same first band). This is just the batch
runner over existing titles.

    python deploy/career_calibrate_bands.py            # dry-run (prints table)
    python deploy/career_calibrate_bands.py --apply    # write to cp_title

Titles with no matching ad evidence are left unchanged. Idempotent — re-running
recomputes from current cp_ad_class evidence. Run from the dev machine.
"""
import re
import sys
from collections import defaultdict

import net_fix  # noqa: F401 — force IPv4 first
import auth
import careerpaths as cp
import careerpaths_v1 as cpv1


def main() -> None:
    apply = "--apply" in sys.argv
    cl = auth._client(service=True)
    rows = list(cl.table("cp_title").select(
        "title_id,family_id,name_en,primary_ssyk,lo_pct,mid_pct,hi_pct,raw_variants,published"
    ).execute().data or [])
    titles = [t for t in rows if re.match(r"^\d+-\d+$", t["title_id"])]

    by_ssyk: dict = defaultdict(list)
    for t in titles:
        by_ssyk[str(t["primary_ssyk"])].append(t)

    report, updated = [], 0
    for ssyk, ts in by_ssyk.items():
        recs = cpv1.ad_class_for_ssyk(ssyk)
        for t in ts:
            names = [t["name_en"]] + list(t.get("raw_variants") or [])
            want = {str(n).strip().lower() for n in names if n}
            n = sum(1 for r in recs if (r.get("norm_title") or "").strip().lower() in want)
            band = cpv1.calibrate_band(ssyk, names, records=recs)
            old = f"{t['lo_pct']}/{t['mid_pct']}/{t['hi_pct']}"
            if band and apply:
                cl.table("cp_title").update(
                    {"lo_pct": str(band[0]), "mid_pct": str(band[1]), "hi_pct": str(band[2])}
                ).eq("title_id", t["title_id"]).execute()
                updated += 1
            report.append((t["family_id"], t["title_id"], t["name_en"], old, band, n))

    for fam, tid, name, old, band, n in sorted(report, key=lambda r: (r[0], r[1])):
        if band is None:
            print(f"SKIP {fam:15} {tid:8} {name[:32]:32} {old:9} no ad evidence")
        else:
            print(f"CAL  {fam:15} {tid:8} {name[:32]:32} {old:9} -> "
                  f"{band[0]}/{band[1]}/{band[2]:<3} n={n}")
    print(f"\n{'APPLIED' if apply else 'DRY-RUN'} — {updated} updated, "
          f"{sum(1 for r in report if r[4] is None)} skipped, {len(report)} total")
    if apply:
        try:
            cp._clear_cache()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()
