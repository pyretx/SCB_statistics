"""Tests for core.interp.SalaryCurve — the monotone salary-percentile curve.

Runnable standalone: `python tests/test_interp.py` (no pytest required). Each
check asserts one of the three hard guarantees or an edge case.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interp import SalaryCurve, curve_from_stats  # noqa: E402

# A realistic Swedish occupation shape (monthly SEK, right-skewed).
SWE = {10: 32000, 25: 36000, 50: 42000, 75: 51000, 90: 63000}


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol * max(1.0, abs(b))


def test_exact_recovery():
    """Published points are returned exactly and tagged 'published'."""
    c = SalaryCurve(SWE)
    for p, v in SWE.items():
        cp = c.value_at(p)
        assert approx(cp.value, v), f"P{p}: {cp.value} != {v}"
        assert cp.kind == "published", f"P{p} kind={cp.kind}"


def test_monotonic():
    """The curve never decreases across the whole span."""
    c = SalaryCurve(SWE)
    prev = -1.0
    p = 10.0
    while p <= 90.0:
        v = c.value_at(p).value
        assert v >= prev - 1e-9, f"non-monotone at P{p}: {v} < {prev}"
        prev = v
        p += 0.5


def test_interpolated_between_points():
    """A mid value is between its neighbours and tagged 'interpolated'."""
    c = SalaryCurve(SWE)
    cp = c.value_at(60)
    assert SWE[50] < cp.value < SWE[75], f"P60 {cp.value} out of (42000,51000)"
    assert cp.kind == "interpolated"


def test_no_invented_tails():
    """Outside the published span the curve clamps and tags 'extrapolated'."""
    c = SalaryCurve(SWE)
    below, above = c.value_at(5), c.value_at(97)
    assert below.value == SWE[10] and below.kind == "extrapolated"
    assert above.value == SWE[90] and above.kind == "extrapolated"


def test_percentile_at_inverse():
    """percentile_at inverts value_at within the span; None outside it."""
    c = SalaryCurve(SWE)
    # a salary at a known point maps back near that percentile
    p = c.percentile_at(42000)
    assert p is not None and 48 <= p <= 52, f"median inverse p={p}"
    assert c.percentile_at(1000) is None      # below P10 salary
    assert c.percentile_at(999999) is None     # above P90 salary


def test_band_reports_kinds():
    """band() returns salaries + per-edge source kinds (published vs interpolated)."""
    c = SalaryCurve(SWE)
    b = c.band(50, 65, 85)
    assert b["lo_kind"] == "published"          # P50 is a known point
    assert b["mid_kind"] == "interpolated"      # P65 is between points
    assert b["lo_salary"] < b["mid_salary"] < b["hi_salary"]


def test_degenerate_inputs():
    """<2 points → not ok; missing/None values are dropped, not crashed."""
    assert not SalaryCurve({10: 30000}).ok
    assert not SalaryCurve({}).ok
    c = curve_from_stats({"p10": 30000, "p25": None, "median": 40000,
                          "p75": 50000, "p90": None})
    assert c.ok and c.span == (10, 75)          # None points omitted


def test_curve_from_stats_row():
    """Builds from a framework stats row using p10/p25/median/p75/p90."""
    row = {"p10": 32000, "p25": 36000, "median": 42000, "p75": 51000, "p90": 63000}
    c = curve_from_stats(row)
    assert c.ok and approx(c.value_at(50).value, 42000)


def test_software_shape_wider_spread():
    """A wider ICT spread stays monotone and exact (sanity on a 2nd shape)."""
    ict = {10: 38000, 25: 44000, 50: 52000, 75: 64000, 90: 82000}
    c = SalaryCurve(ict)
    for p, v in ict.items():
        assert approx(c.value_at(p).value, v)
    assert c.value_at(70).value > c.value_at(55).value


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
