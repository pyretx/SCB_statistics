"""Reusable country-page framework (see docs/architecture.md).

A country = (CountryConfig + CountryProvider). ``core.page.render_country(cfg)``
renders the one shared skeleton; providers turn each country's API into the one
normalized model in ``core.model``. Built to run *alongside* the existing Sweden
and France page scripts without touching them.
"""
