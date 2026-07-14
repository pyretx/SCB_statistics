"""Career Paths v1 — offline AI classification (Anthropic Claude, batch).

Given PII-scrubbed ads (career_jobtech.scrub), infers per ad: seniority level,
people-management responsibility, minimum experience, a normalised English job
title, and up to ~6 skill phrases (the JobTech structured skills are usually
empty, so the model reads the scrubbed description). Runs OFFLINE / admin-triggered
only — never per user request.

Calls the Anthropic Messages API over HTTPS (no SDK dependency). The key is read
from secrets ([anthropic] api_key) or the ANTHROPIC_API_KEY env var and is never
printed. Default model = Haiku 4.5 (cheapest, per the v1 config).
"""
from __future__ import annotations

import json
import os
import re

import requests

try:
    import streamlit as st
except Exception:  # noqa: BLE001
    st = None

_MODEL = "claude-haiku-4-5-20251001"
_URL = "https://api.anthropic.com/v1/messages"
_SENIORITY = {"junior", "mid", "senior", "lead", "principal", "manager"}


def _key() -> str | None:
    try:
        if st is not None:
            k = st.secrets.get("anthropic", {}).get("api_key")
            if k:
                return str(k)
    except Exception:  # noqa: BLE001
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def available() -> bool:
    return bool(_key())


def _prompt(ads: list[dict]) -> str:
    blocks = []
    for i, a in enumerate(ads):
        desc = (a.get("description") or "")[:1500]
        blocks.append(f"[{i}] TITLE: {a.get('headline', '')}\nAD: {desc}")
    body = "\n\n".join(blocks)
    instr = (
        "You classify Swedish job advertisements. For EACH numbered ad below, output one "
        "JSON object with keys:\n"
        '  idx (int, the ad number),\n'
        '  seniority (one of: junior, mid, senior, lead, principal, manager),\n'
        '  mgmt (true only if the role has formal people-management responsibility),\n'
        '  years (minimum years of relevant experience requested, integer, or null),\n'
        '  skills (array of up to 6 short English skill/requirement phrases),\n'
        '  norm_title (a short normalised English job title).\n'
        "Judge only from the ad text. Interpret words like Lead/Manager/Chef in context "
        "(not every 'Lead' means people management). Return ONLY a JSON array of these "
        "objects, nothing else."
    )
    return f"{instr}\n\n{body}"


def _parse(text: str) -> list[dict]:
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        arr = json.loads(m.group(0))
        return arr if isinstance(arr, list) else []
    except Exception:  # noqa: BLE001
        return []


def classify(ads: list[dict], model: str | None = None, batch: int = 8) -> list[dict]:
    """Classify scrubbed ads. Returns one dict per input ad (empty AI fields on
    failure). Never raises."""
    key = _key()
    if not key or not ads:
        return []
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    out: list[dict] = []
    for start in range(0, len(ads), batch):
        chunk = ads[start:start + batch]
        payload = {"model": model or _MODEL, "max_tokens": 2000,
                   "messages": [{"role": "user", "content": _prompt(chunk)}]}
        arr = []
        try:
            r = requests.post(_URL, headers=headers, json=payload, timeout=90)
            r.raise_for_status()
            arr = _parse(r.json()["content"][0]["text"])
        except Exception as e:  # noqa: BLE001
            print(f"[career_ai] batch @{start} failed: {e}")
        by_idx = {o.get("idx"): o for o in arr if isinstance(o, dict)}
        for j, a in enumerate(chunk):
            o = by_idx.get(j, {})
            sen = o.get("seniority")
            out.append({
                "id": a.get("id"), "headline": a.get("headline"), "ssyk": a.get("ssyk"),
                "seniority": sen if sen in _SENIORITY else None,
                "mgmt": bool(o.get("mgmt")),
                "years": o.get("years") if isinstance(o.get("years"), int) else None,
                "skills": (o.get("skills") or a.get("skills") or [])[:6],
                "norm_title": o.get("norm_title"),
            })
    return out
