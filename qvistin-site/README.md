# Qvistin corporate homepage (`qvist.in`)

A small, self-contained **static site** — the Qvistin marketing homepage that will
serve `https://qvist.in` (see `docs/qvistin-hosting.md` for how it slots into the
Traefik stack). Converted from the original Claude "Bundled Page" export into a
clean, maintainable, content-driven site: **design/animations preserved**, all copy
externalised, no runtime framework (the 323 KB React-in-browser bundle became a
~15 KB static page).

## Editing the text

All copy lives in **`content.toml`** — the static-site analogue of Salary
Explorer's `content/*.toml`. Edit it, then rebuild:

```bash
cd qvistin-site
python build.py          # renders dist/index.html from content.toml + templates/
```

You can change headings, product cards, the branch-diagram nodes, contact details,
nav/footer, and the brand `accent` colour without touching any HTML/CSS.

## Preview locally

```bash
cd qvistin-site/dist
python -m http.server 8721
# open http://localhost:8721
```

## Layout

```
qvistin-site/
├── content.toml            # ← EDIT THIS: all page text + product/nav/diagram data
├── build.py                # renders dist/ from content.toml + templates/ (Jinja2)
├── templates/
│   └── index.html.j2        # page structure + inline SVG icons (design, rarely edited)
├── static/
│   ├── css/site.css         # all styling (converted from the original inline styles)
│   └── js/site.js           # branch-diagram hover, topic chips, contact form → mailto
├── dist/                    # BUILD OUTPUT — this folder is what the web server serves
└── README.md
```

## Notes

- **Fonts** load from Google Fonts (Manrope + JetBrains Mono), matching the
  original. Can be self-hosted later if we want zero external requests.
- **Contact form** has no backend — on submit it composes a `mailto:` to the
  address in `content.toml` and opens the visitor's mail app. Swap in a form
  service (Formspree/Basin) or a small endpoint later if we want inbox delivery.
- Placeholder links (`href = "#"` for GitHub / LinkedIn / Learn More) are marked
  `TODO` in `content.toml` — set the real URLs when available.
- **Deploy:** `dist/` is copied to `/srv/qvistin-site` on the server and served by a
  small `nginx:alpine` container via Traefik (`deploy/docker-compose.qvistin-site.yml`,
  to be added — see `docs/qvistin-hosting.md`). Rebuild (`python build.py`) before
  deploying so `dist/` reflects the latest `content.toml`.
```
