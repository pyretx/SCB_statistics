"""Lithuania provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def LithuaniaProvider():
    return EurostatSESProvider("lithuania", "EUR")


def _leaves(lang="EN"):
    return leaves("lithuania", lang)
