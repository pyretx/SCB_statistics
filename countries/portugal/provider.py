"""Portugal provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def PortugalProvider():
    return EurostatSESProvider("portugal", "EUR")


def _leaves(lang="EN"):
    return leaves("portugal", lang)
