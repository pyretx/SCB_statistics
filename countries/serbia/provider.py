"""Serbia provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def SerbiaProvider():
    return EurostatSESProvider("serbia", "EUR")


def _leaves(lang="EN"):
    return leaves("serbia", lang)
