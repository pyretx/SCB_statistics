"""Lithuania — Eurostat SES (earn_ses_21), geo=LT. Thin wrapper over the shared
countries/eurostat_ses.py engine."""
import os

from countries import eurostat_ses as _e

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "lithuania_earnings.json.gz")
GEO = "LT"


def build(out_path: str = OUT, log=print) -> dict:
    return _e.build_country(GEO, out_path, log)


def bundled_info(path: str = OUT) -> dict:
    return _e.bundled_info(path)


def years() -> list:
    return bundled_info().get("years") or [2006, 2022]


if __name__ == "__main__":
    print(build())
