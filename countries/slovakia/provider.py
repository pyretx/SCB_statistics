"""Slovakia provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def SlovakiaProvider():
    return EurostatSESProvider("slovakia", "EUR")


def _leaves(lang="EN"):
    return leaves("slovakia", lang)
