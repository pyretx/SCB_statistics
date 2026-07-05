"""Occupation-classification hierarchy helpers (shared by the sidebar drill-down
and the code browser).

A classification is just a ``{code: name}`` dict spanning several levels (e.g.
STYRK/SSYK 1→2→3→4 digit, France PCS 1→2→4). Parent/child links are derived
from code prefixes, so any number of levels — and gaps — work automatically.
"""
from __future__ import annotations


def parent_of(code: str, present: set) -> str | None:
    """Longest present code that is a proper prefix of ``code`` (its direct
    parent), or None if ``code`` is a top-level root."""
    for L in range(len(code) - 1, 0, -1):
        if code[:L] in present:
            return code[:L]
    return None


def build(tree: dict) -> tuple[list, dict]:
    """Return ``(roots, children)`` for a ``{code: name}`` classification:
    ``roots`` = top-level codes; ``children[code]`` = its direct child codes."""
    present = set(tree)
    children: dict[str, list] = {}
    roots: list[str] = []
    for c in tree:
        p = parent_of(c, present)
        (roots if p is None else children.setdefault(p, [])).append(c)
    return roots, children


def group_lengths(tree: dict, leaf_len: int) -> list[int]:
    """Sorted distinct code lengths that are GROUP levels (shorter than a leaf),
    e.g. [1, 2, 3] for STYRK, [1, 2] for France PCS."""
    return sorted({len(c) for c in tree if len(c) < leaf_len})
