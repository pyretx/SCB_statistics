"""Malta provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def MaltaProvider():
    return EurostatSESProvider("malta", "EUR")


def _leaves(lang="EN"):
    return leaves("malta", lang)
