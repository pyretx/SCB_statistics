"""Latvia provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def LatviaProvider():
    return EurostatSESProvider("latvia", "EUR")


def _leaves(lang="EN"):
    return leaves("latvia", lang)
