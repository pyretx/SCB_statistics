"""Build us_oews.json.gz — US BLS OEWS wages by SOC occupation (CLI shim).

The actual build logic now lives in countries/us/build.py (a SHIPPED module, so
the admin panel can trigger a refresh at runtime). This file is just the offline
CLI entry point; it stays dockerignored.

A "scope" is the framework's 'sector' slot. OEWS publishes three cuts that do
NOT combine (there is no clean state x industry), so all three fold into one
mutually-exclusive scope list:
  - United States, all industries   -> key "US"        (oesm{YY}nat.zip)
  - each state, all industries       -> key = 2-letter state (oesm{YY}st.zip)
  - each national NAICS industry     -> key = "IND"+naics (oesm{YY}in4.zip:
    sector + 3-digit + 4-digit levels — the coverage/suppression sweet spot)

Run once (needs openpyxl locally; also a runtime dep now — see requirements):
    python build_us_oews.py
"""
from countries.us.build import build

if __name__ == "__main__":
    build(log=print)
