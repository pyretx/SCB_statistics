# Editing page text

All user-facing text on the **home page** and **sign-in box** lives in this
folder — edit the `.toml` files, save, and refresh the app. **No code changes,
no redeploy of logic.** Layout, charts and behaviour are untouched by these files.

| File | What it controls |
|------|------------------|
| [`home.toml`](home.toml) | The whole start page: brand/badge, header buttons, hero title + intro, the three KPI figures, the live-preview card, the country tiles (names, bullets, sources, badges), and the footer note. |
| [`auth.toml`](auth.toml) | The Sign in / Create account dialog: the blue panel (headline + checklist), the form labels & placeholders, button text, the terms line, and all success/error messages. |

## How it works
- Each file is grouped into `[sections]` (e.g. `[hero]`, `[countries]`). A key is
  `name = "the text"`. Lines starting with `#` are comments/help.
- A few values contain `{name}` or `{err}` — those are placeholders the app fills
  in (e.g. `open_cta = "Open {name} →"`). Keep the `{…}` part.
- `home.toml → [[countries.tiles]]` has one block per card. `name`, `native`,
  `source`, `points`, `badge_text` are safe to edit; `num`, `iso`, `page`,
  `live`, badge colours are wiring/styling — leave them unless you know why.

## Section taxonomy (also used by future country pages)
`brand · header · hero · kpis · countries · filters · charts · tables ·
messages · source · help · footer`

The home page uses the sections it needs. A future country data-page would add a
`content/countries/<slug>.toml` with the same shape (filters/charts/tables/…),
read the same way via `content.load("countries/<slug>")`.

> Country **data-page** micro-labels (sidebar filters, tab names, table headers)
> currently live in `core/i18n.py` + each `countries/<slug>/config.py` (`i18n=`),
> because they’re short and translated per language. They can migrate into this
> `content/` system later using the same taxonomy.
