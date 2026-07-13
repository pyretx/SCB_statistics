"""Ireland provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def IrelandProvider():
    return EurostatSESProvider("ireland", "EUR")


def _leaves(lang="EN"):
    return leaves("ireland", lang)
