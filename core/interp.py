"""Monotone salary-percentile interpolation (Career Paths beta + reusable).

Salary Explorer publishes only a handful of percentile points per occupation
(Sweden: P10, P25, P50/median, P75, P90). Career Paths needs a *continuous* curve
to place estimated career-level bands on — but it must never fabricate or distort
the official statistics. This module fits a monotone curve through the published
points with three hard guarantees:

  1. **Exactness** — the published points are recovered exactly.
  2. **Monotonicity** — the curve never decreases (pay rises with percentile).
  3. **No invented tails** — outside the published percentile span the curve is
     clamped and every returned value is tagged so the UI can flag it.

Method: monotone cubic Hermite interpolation (Fritsch–Carlson tangents) on
**log-salary** (pay is right-skewed, so log-space avoids overshoot and keeps the
interpolation realistic). Pure-Python (math only) — no numpy/scipy dependency.

Every returned value carries a ``kind``:
  "published"    — a value at an exactly-known percentile
  "interpolated" — between two known percentiles
  "extrapolated" — outside the known span (clamped; UI must warn)

Nothing here reads or writes app state; it is a pure numeric utility with tests
in tests/test_interp.py.
"""
from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass


@dataclass(frozen=True)
class CurvePoint:
    value: float
    kind: str            # "published" | "interpolated" | "extrapolated"


def _fritsch_carlson_tangents(xs: list[float], ys: list[float]) -> list[float]:
    """Monotone tangents m[i] for cubic Hermite through (xs, ys), xs strictly
    increasing. Guarantees the resulting spline is monotone when the data is."""
    n = len(xs)
    if n == 1:
        return [0.0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    delta = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = delta[0], delta[-1]
    for i in range(1, n - 1):
        if delta[i - 1] * delta[i] <= 0:
            m[i] = 0.0                     # local extremum → flat tangent (monotone)
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / delta[i - 1] + w2 / delta[i])
    return m


class SalaryCurve:
    """A monotone salary curve fitted through published (percentile, salary)
    points. Percentiles are 0–100 (e.g. 10, 25, 50, 75, 90)."""

    def __init__(self, points: dict[float, float]):
        # keep only finite, positive salaries at valid percentiles, sorted by pct
        clean = sorted((float(p), float(v)) for p, v in points.items()
                       if v is not None and math.isfinite(v) and v > 0
                       and p is not None and math.isfinite(p))
        # de-duplicate percentiles (keep first) and enforce strictly increasing pct
        xs: list[float] = []
        vs: list[float] = []
        for p, v in clean:
            if xs and p == xs[-1]:
                continue
            xs.append(p)
            vs.append(v)
        self._xs = xs
        self._vs = vs
        self._logs = [math.log(v) for v in vs]
        self._m = _fritsch_carlson_tangents(xs, self._logs) if len(xs) >= 2 else [0.0] * len(xs)
        self._known = set(xs)

    @property
    def ok(self) -> bool:
        """True when at least two published points exist (curve is usable)."""
        return len(self._xs) >= 2

    @property
    def span(self) -> tuple[float, float]:
        """(min, max) published percentile."""
        return (self._xs[0], self._xs[-1]) if self._xs else (0.0, 0.0)

    def value_at(self, pct: float) -> CurvePoint:
        """Salary at percentile ``pct``. Clamped (and tagged 'extrapolated')
        outside the published span; exact ('published') at a known point."""
        if not self._xs:
            return CurvePoint(float("nan"), "extrapolated")
        lo, hi = self._xs[0], self._xs[-1]
        if pct <= lo:
            return CurvePoint(self._vs[0], "published" if pct == lo else "extrapolated")
        if pct >= hi:
            return CurvePoint(self._vs[-1], "published" if pct == hi else "extrapolated")
        if pct in self._known:
            return CurvePoint(self._vs[self._xs.index(pct)], "published")
        # locate the interval [x[i], x[i+1]] containing pct
        i = bisect_left(self._xs, pct) - 1
        i = max(0, min(i, len(self._xs) - 2))
        x0, x1 = self._xs[i], self._xs[i + 1]
        y0, y1 = self._logs[i], self._logs[i + 1]
        m0, m1 = self._m[i], self._m[i + 1]
        h = x1 - x0
        t = (pct - x0) / h
        # cubic Hermite basis
        h00 = 2 * t ** 3 - 3 * t ** 2 + 1
        h10 = t ** 3 - 2 * t ** 2 + t
        h01 = -2 * t ** 3 + 3 * t ** 2
        h11 = t ** 3 - t ** 2
        logv = h00 * y0 + h10 * h * m0 + h01 * y1 + h11 * h * m1
        return CurvePoint(math.exp(logv), "interpolated")

    def percentile_at(self, salary: float, *, step: float = 0.5) -> float | None:
        """Approximate percentile position of a given salary within the published
        span (monotone → invertible). Returns a percentile in [span], or None if
        the salary is outside the published salary range (tails not invented)."""
        if not self.ok or salary is None or not math.isfinite(salary):
            return None
        lo, hi = self._vs[0], self._vs[-1]
        if salary <= lo or salary >= hi:
            return None
        p_lo, p_hi = self._xs[0], self._xs[-1]
        p = p_lo
        best = None
        while p <= p_hi:
            if self.value_at(p).value >= salary:
                best = p
                break
            p += step
        return round(best, 1) if best is not None else None

    def band(self, lo_pct: float, mid_pct: float, hi_pct: float) -> dict:
        """A career-level salary band from three percentiles → salaries + the
        source tag of each. The caller marks the whole band as a Qvistin estimate;
        this only reports which salary values are published vs interpolated."""
        lo, mid, hi = self.value_at(lo_pct), self.value_at(mid_pct), self.value_at(hi_pct)
        return {
            "lo_pct": lo_pct, "mid_pct": mid_pct, "hi_pct": hi_pct,
            "lo_salary": lo.value, "mid_salary": mid.value, "hi_salary": hi.value,
            "lo_kind": lo.kind, "mid_kind": mid.kind, "hi_kind": hi.kind,
        }


def curve_from_stats(row: dict) -> SalaryCurve:
    """Build a SalaryCurve from a normalized occupation-stats row (the framework's
    p10/p25/median/p75/p90 fields). Missing points are simply omitted."""
    pts = {}
    for pct, key in ((10, "p10"), (25, "p25"), (50, "median"),
                     (75, "p75"), (90, "p90")):
        v = row.get(key)
        if v is not None:
            try:
                pts[pct] = float(v)
            except (TypeError, ValueError):
                pass
    return SalaryCurve(pts)
