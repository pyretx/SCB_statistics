"""Build the static Qvistin homepage from content.toml + templates/.

A static site has no server runtime, so the editable copy in content.toml is
rendered into dist/index.html at build time (the static analogue of Salary
Explorer's content/*.toml). Design/layout live in templates/index.html.j2 and
static/. Run:  python build.py   → writes dist/ (index.html + static/), which is
what nginx serves.
"""
from __future__ import annotations

import shutil
import tomllib
from pathlib import Path
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

# Foundation node + branch-path geometry (from the original diagram logic).
_F = (500, 392)


def _branches(nodes: list[dict]) -> list[dict]:
    out = []
    for i, n in enumerate(nodes):
        x, y, live = int(n["x"]), int(n["y"]), bool(n.get("live"))
        c1x = _F[0] + (x - _F[0]) * 0.12
        c1y = _F[1] - 130
        c2x = x - (x - _F[0]) * 0.10
        c2y = y + 120
        end_y = y + (13 if live else 10)
        path = f"M{_F[0]},{_F[1] - 26} C{c1x:.1f},{c1y} {c2x:.1f},{c2y} {x},{end_y}"
        out.append({
            "label": n["label"], "x": x, "y": y, "live": live,
            "href": (n.get("href") or "").strip(),
            "path": path,
            "r": 13 if live else 9,
            "fill": "#12151A" if live else "#FAFAF9",
            "stroke": "transparent" if live else "#C6CBCF",
            "label_left": round(x / 10, 2),
            "label_top": round((y - 24) / 430 * 100, 2),
            "path_delay": round(0.15 + i * 0.12, 2),
            "node_delay": round(0.9 + i * 0.12, 2),
        })
    return out


_FAVICON = quote(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">'
    '<circle cx="14" cy="13" r="8" stroke="#12151A" stroke-width="2.4"/>'
    '<path d="M19.5 19.5 L24 24" stroke="#12151A" stroke-width="2.4" stroke-linecap="round"/>'
    '<path d="M24 24 L28 21" stroke="#23716B" stroke-width="2.4" stroke-linecap="round"/>'
    '<path d="M24 24 L26 29" stroke="#23716B" stroke-width="2.4" stroke-linecap="round"/>'
    '<circle cx="29.2" cy="20" r="1.9" fill="#23716B"/>'
    '<circle cx="26.8" cy="30.2" r="1.9" fill="#23716B"/></svg>'
)


def build(log=print) -> None:
    content = tomllib.loads((ROOT / "content.toml").read_text(encoding="utf-8"))
    ctx = dict(content)
    ctx["branches"] = _branches(content.get("diagram", {}).get("node", []))
    ctx["favicon_svg"] = _FAVICON

    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True, lstrip_blocks=True,
    )
    html = env.get_template("index.html.j2").render(**ctx)

    # Clean DIST's contents (not the dir itself — a running preview server may
    # hold a handle on the directory on Windows).
    DIST.mkdir(parents=True, exist_ok=True)
    for child in DIST.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    (DIST / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(ROOT / "static", DIST / "static")
    log(f"built {DIST/'index.html'}  ({len(html)} bytes, "
        f"{len(ctx['branches'])} branches, {len(content.get('products', {}).get('item', []))} products)")


if __name__ == "__main__":
    build()
