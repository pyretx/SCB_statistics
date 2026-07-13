"""Serbia config — Eurostat SES (ISCO major groups x sex). BETA."""
from countries.eurostat_ses import make_config
from .build import years

CONFIG = make_config(
    slug="serbia", name="Serbia", native="Srbija", iso="rs",
    currency="EUR", currency_suffix="€", money_prefix=False, years=years(),
)
