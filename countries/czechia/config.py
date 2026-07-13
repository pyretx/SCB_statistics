"""Czechia config — Eurostat SES (ISCO major groups x sex x 2006-2022). BETA."""
from countries.eurostat_ses import make_config
from .build import years

CONFIG = make_config(
    slug="czechia", name="Czechia", native="Cesko", iso="cz",
    currency="EUR", currency_suffix="€", money_prefix=False, years=years(),
)
