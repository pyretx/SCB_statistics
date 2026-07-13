"""Romania provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def RomaniaProvider():
    return EurostatSESProvider("romania", "EUR")


def _leaves(lang="EN"):
    return leaves("romania", lang)
