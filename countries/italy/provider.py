"""Italy provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def ItalyProvider():
    return EurostatSESProvider("italy", "EUR")


def _leaves(lang="EN"):
    return leaves("italy", lang)
