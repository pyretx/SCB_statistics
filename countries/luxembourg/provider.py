"""Luxembourg provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def LuxembourgProvider():
    return EurostatSESProvider("luxembourg", "EUR")


def _leaves(lang="EN"):
    return leaves("luxembourg", lang)
