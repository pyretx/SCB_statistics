"""Force IPv4 for outbound HTTP (urllib3 / requests / most SDKs on top of them).

Why: when the local network advertises IPv6 but the v6 route is broken (this
dev machine), every FRESH connection to a dual-stack host (api.scb.se,
*.supabase.co, api.insee.fr, …) first waits ~21s for the IPv6 connect to time
out before falling back to IPv4 — measured: IPv6 connect 21.07s FAIL, IPv4
0.01s OK. Browsers dodge this with Happy Eyeballs; urllib3 tries the addresses
sequentially with the full connect timeout each.

Forcing IPv4 is safe for this app: every data source it talks to serves IPv4.
Imported for its side effect — `import net_fix` early (app.py, CLI builds).
"""
import socket

try:
    from urllib3.util import connection as _u3c

    def _ipv4_only():
        return socket.AF_INET

    _u3c.allowed_gai_family = _ipv4_only
except Exception:                       # never break the app over a net tweak
    pass

try:  # httpx (Supabase SDK) resolves via getaddrinfo too — filter AAAA there as
    # well by preferring IPv4 results process-wide.
    _orig_gai = socket.getaddrinfo

    def _gai_ipv4_first(host, port, family=0, type=0, proto=0, flags=0):
        res = _orig_gai(host, port, family, type, proto, flags)
        v4 = [r for r in res if r[0] == socket.AF_INET]
        return v4 or res

    socket.getaddrinfo = _gai_ipv4_first
except Exception:
    pass
