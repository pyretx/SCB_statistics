"""Austria provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def AustriaProvider():
    return EurostatSESProvider("austria", "EUR")


def _leaves(lang="EN"):
    return leaves("austria", lang)
