"""Bulgaria provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def BulgariaProvider():
    return EurostatSESProvider("bulgaria", "EUR")


def _leaves(lang="EN"):
    return leaves("bulgaria", lang)
