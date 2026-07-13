"""Poland provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def PolandProvider():
    return EurostatSESProvider("poland", "EUR")


def _leaves(lang="EN"):
    return leaves("poland", lang)
