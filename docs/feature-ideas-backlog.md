# Feature ideas backlog

Structured backlog of feature ideas for Salary Explorer. Each item keeps the
original idea plus technical notes tied to the codebase and data sources.

> **Why this lives in git:** memory-tool notes only exist on a single session's
> ephemeral container and are lost when it's reclaimed. Committing the backlog
> here means every future session — remote or local — can read it.

---

## 1. Cross-country profession comparison — *the big one*

Compare the same profession across countries.

- **Feasibility:** official code-translation tables largely exist. Most of our
  countries use national ISCO-08 variants (SSYK, STYRK, DISCO, SKP, …), and
  agencies publish correspondence keys (e.g. SCB publishes SSYK↔ISCO).
- **Plan of record:** pre-connect via official correspondence tables where they
  exist; AI-suggest the remaining mappings; admin review/adjust UI (reuse the
  existing career-admin review pattern).
- **Display features:** monthly/annual toggle; currency choice (FX is already
  modeled as a dataset type in the compliance register); same-year alignment;
  social costs / taxes as a future step.
- **Effort:** large — deserves its own planning session.

## 2. T&C checkbox at sign-up + simple terms

Required terms consent at sign-up plus a plain terms page.

- The sign-up dialog already has a terms caption placeholder.
- Copy belongs in `content/*.toml`, like the rest of the landing/auth text.
- **Gate:** one of the two items that must land before opening sign-up beyond
  approved beta users.

## 3. Career paths browser

A "navigate, don't search" section in the Code browser.

- Driven by the existing `cp_family` / `cp_title` hierarchy.

## 4. Account self-service

- User-facing **password reset** (currently admin-only). Supabase's reset-email
  flow can reuse our signup-confirmation token pattern.
- **Profile picture.**

## 5. Security review of the public forms — *gate*

Review public forms before opening sign-up beyond approved beta users.

- Explicitly positioned as a gate before widening access.
- Scope includes the new `sb_refresh` cookie flow — fresh attack surface.

## 6. Full Platsbanken pull

- Verify no family's query exceeds the JobSearch API's 2,000-results cap.
- Mitigation: query-splitting by occupation group / region / date window.
- **Effort:** ~half a day.

## 7. *(open)*

Slot intentionally left open for future ideas — append here as they come up.

---

## Suggested "next up" cluster

Items **2 + 5** gate opening the app to unapproved users; item **6** is roughly
a half-day job. Those three are the natural next cluster. Item **1** (the
comparison feature) deserves a dedicated planning session of its own.
