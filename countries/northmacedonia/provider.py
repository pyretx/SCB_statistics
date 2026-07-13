"""North Macedonia provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def NorthmacedoniaProvider():
    return EurostatSESProvider("northmacedonia", "EUR")


def _leaves(lang="EN"):
    return leaves("northmacedonia", lang)
