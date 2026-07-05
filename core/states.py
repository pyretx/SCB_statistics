"""Shared empty / loading / error states + the exclusive-view mount.

The view-mount is the fix learned from the Swedish page: full-page views
(guides, code browsers, admin panels) render into ONE st.empty() so they clear
themselves on a normal data run instead of ghosting behind the charts.
"""
from __future__ import annotations

import contextlib

import streamlit as st


def view_mount():
    """A single st.empty() placeholder. Render an exclusive full-page view into
    ``mount.container()`` and st.stop(); on a normal run it's left empty, which
    clears whatever a previous run put there."""
    return st.empty()


def prompt(msg: str):
    st.info(msg)


def no_data(msg: str = "No data for this selection."):
    st.warning(msg)


def error(msg: str):
    st.error(msg)


@contextlib.contextmanager
def loading(msg: str = "Fetching data…"):
    with st.spinner(msg):
        yield
