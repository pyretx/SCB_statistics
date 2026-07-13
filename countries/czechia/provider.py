"""Czechia provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def CzechiaProvider():
    return EurostatSESProvider("czechia", "EUR")


def _leaves(lang="EN"):
    return leaves("czechia", lang)
