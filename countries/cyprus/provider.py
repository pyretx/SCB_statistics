"""Cyprus provider — Eurostat SES engine (shared)."""
from countries.eurostat_ses import EurostatSESProvider, leaves


def CyprusProvider():
    return EurostatSESProvider("cyprus", "EUR")


def _leaves(lang="EN"):
    return leaves("cyprus", lang)
