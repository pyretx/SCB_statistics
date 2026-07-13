"""Hungary provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def HungaryProvider():
    return EurostatSESProvider("hungary", "EUR")


def _leaves(lang="EN"):
    return leaves("hungary", lang)
