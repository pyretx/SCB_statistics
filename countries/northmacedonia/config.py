"""North Macedonia config — Eurostat SES (ISCO major groups x sex). BETA."""
from countries.eurostat_ses import make_config
from .build import years

CONFIG = make_config(
    slug="northmacedonia", name="North Macedonia", native="Severna Makedonija", iso="mk",
    currency="EUR", currency_suffix="€", money_prefix=False, years=years(),
)
