"""Local dev tool — fill English labels (en) for PCS-ESE occupation names in
pcs_labels.json using the Anthropic API. Reads the key from .streamlit/
secrets.toml ([anthropic] api_key). NOT used by the deployed container.

Only translates entries whose "en" is still null, so it's safe to re-run.

Setup:  pip install --user anthropic   (key in .streamlit/secrets.toml)
Run:    python build_pcs_translations.py
"""
import io
import json
import os
import sys
import time
import tomllib

import anthropic

HERE      = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "pcs_labels.json")
SECRETS   = os.path.join(HERE, ".streamlit", "secrets.toml")
MODEL     = "claude-haiku-4-5-20251001"
BATCH     = 40   # labels are short → larger batches are fine


def load_key() -> str:
    with open(SECRETS, "rb") as f:
        key = tomllib.load(f).get("anthropic", {}).get("api_key", "")
    if not key or "PASTE_" in key:
        sys.exit("No Anthropic api_key found in .streamlit/secrets.toml [anthropic].")
    return key


def _call(client, prompt: str) -> dict:
    resp = client.messages.create(
        model=MODEL, max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        text = text[4:] if text.startswith("json") else text
    return json.loads(text)


def translate_batch(client, items: dict) -> dict:
    prompt = (
        "These are official French occupational classification labels (INSEE "
        "PCS-ESE, the French socio-professional categories). Translate each into "
        "natural, professional English as used in labour statistics. Keep them "
        "concise noun phrases; do not add notes or expand abbreviations beyond "
        "what's needed for clarity. Return ONLY a JSON object mapping each key to "
        "its English label, no commentary.\n\n"
        + json.dumps(items, ensure_ascii=False)
    )
    return _call(client, prompt)


def main():
    client = anthropic.Anthropic(api_key=load_key())
    data = json.load(io.open(DATA_FILE, encoding="utf-8"))
    labels = data["labels"]

    todo = [c for c, v in labels.items() if v.get("fr") and not v.get("en")]
    print(f"{len(todo)} PCS labels to translate (model {MODEL})")

    done = 0
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        items = {c: labels[c]["fr"] for c in chunk}
        try:
            out = translate_batch(client, items)
        except Exception as e:
            print(f"  ! batch {i}-{i+len(chunk)} failed: {e} — retrying once")
            time.sleep(3)
            try:
                out = translate_batch(client, items)
            except Exception as e2:
                print(f"  !! skipped batch: {e2}")
                continue
        for c in chunk:
            if c in out and str(out[c]).strip():
                labels[c]["en"] = str(out[c]).strip()
                done += 1
        json.dump(data, io.open(DATA_FILE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)   # save after every batch
        print(f"  {done}/{len(todo)} done")
        time.sleep(0.5)

    total = sum(1 for v in labels.values() if v.get("en"))
    print(f"Finished. en filled: {total}/{len(labels)}")


if __name__ == "__main__":
    main()
