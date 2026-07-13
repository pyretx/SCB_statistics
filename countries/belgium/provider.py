"""Belgium provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def BelgiumProvider():
    return EurostatSESProvider("belgium", "EUR")


def _leaves(lang="EN"):
    return leaves("belgium", lang)
