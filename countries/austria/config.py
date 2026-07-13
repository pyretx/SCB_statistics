"""Austria config — Eurostat SES (ISCO major groups x sex x 2006-2022). BETA."""
from countries.eurostat_ses import make_config
from .build import years

CONFIG = make_config(
    slug="austria", name="Austria", native="Osterreich", iso="at",
    currency="EUR", currency_suffix="€", money_prefix=False, years=years(),
)
