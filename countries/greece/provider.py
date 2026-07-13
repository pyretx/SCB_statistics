"""Greece provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def GreeceProvider():
    return EurostatSESProvider("greece", "EUR")


def _leaves(lang="EN"):
    return leaves("greece", lang)
