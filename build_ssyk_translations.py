"""Local dev tool — fill in English translations (desc_en) for SSYK descriptions
using the Anthropic API. Reads the key from .streamlit/secrets.toml ([anthropic]
api_key). NOT used by the deployed container.

It only translates nodes whose desc_en is still empty, so it's safe to re-run
(e.g. after adding more scraped data) and it skips anything already done.

Setup:
    pip install --user anthropic
    # put your key in .streamlit/secrets.toml under [anthropic] api_key
Run:
    python build_ssyk_translations.py
"""
import json
import io
import os
import sys
import time
import tomllib
import anthropic

HERE      = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "ssyk_descriptions.json")
SECRETS   = os.path.join(HERE, ".streamlit", "secrets.toml")
MODEL     = "claude-haiku-4-5-20251001"   # cheap + good for translation
BATCH     = 15                            # descriptions per API call


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
        "Translate each Swedish occupational description into natural, professional "
        "English. Keep it faithful and concise. Preserve line breaks (\\n). "
        "Return ONLY a JSON object mapping each key to its English translation, "
        "no commentary.\n\n"
        + json.dumps(items, ensure_ascii=False)
    )
    return _call(client, prompt)


def translate_syn_batch(client, items: dict) -> dict:
    prompt = (
        "Each key maps to a list of Swedish job titles (synonyms for an occupation). "
        "Translate each title into natural English. Keep the same number of items in "
        "the same order. Return ONLY a JSON object mapping each key to the list of "
        "English titles, no commentary.\n\n"
        + json.dumps(items, ensure_ascii=False)
    )
    return _call(client, prompt)


def main():
    client = anthropic.Anthropic(api_key=load_key())
    data = json.load(io.open(DATA_FILE, encoding="utf-8"))
    nodes = data["nodes"]

    todo = [c for c, n in nodes.items() if n.get("desc_sv") and not n.get("desc_en")]
    print(f"{len(todo)} descriptions to translate (model {MODEL})")

    done = 0
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        items = {c: nodes[c]["desc_sv"] for c in chunk}
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
            if c in out and out[c].strip():
                nodes[c]["desc_en"] = out[c].strip()
                done += 1
        json.dump(data, io.open(DATA_FILE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)   # save after every batch
        print(f"  {done}/{len(todo)} done")
        time.sleep(0.5)

    total = sum(1 for n in nodes.values() if n.get("desc_en"))
    print(f"Descriptions done. desc_en filled: {total}")

    # ── Synonyms: keep Swedish for search, add English for display ─────────────
    syn_todo = [c for c, n in nodes.items()
                if n.get("synonyms") and not n.get("synonyms_en")]
    print(f"\n{len(syn_todo)} occupations' synonym lists to translate")
    SBATCH = 8
    sdone = 0
    for i in range(0, len(syn_todo), SBATCH):
        chunk = syn_todo[i:i + SBATCH]
        items = {c: nodes[c]["synonyms"] for c in chunk}
        try:
            out = translate_syn_batch(client, items)
        except Exception as e:
            print(f"  ! syn batch failed: {e} — retrying once")
            time.sleep(3)
            try:
                out = translate_syn_batch(client, items)
            except Exception as e2:
                print(f"  !! skipped: {e2}")
                continue
        for c in chunk:
            en = out.get(c)
            if isinstance(en, list) and en:
                nodes[c]["synonyms_en"] = [str(x).strip() for x in en if str(x).strip()]
                sdone += 1
        json.dump(data, io.open(DATA_FILE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  {sdone}/{len(syn_todo)} synonym lists done")
        time.sleep(0.5)
    print(f"Finished. synonyms_en filled for {sum(1 for n in nodes.values() if n.get('synonyms_en'))} occupations")


if __name__ == "__main__":
    main()
