"""Croatia provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def CroatiaProvider():
    return EurostatSESProvider("croatia", "EUR")


def _leaves(lang="EN"):
    return leaves("croatia", lang)
