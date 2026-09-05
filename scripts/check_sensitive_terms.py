#!/usr/bin/env python3
import argparse, json
from pathlib import Path


def load_terms(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [str(x) for x in data.get("blocked_terms", []) if str(x)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text_file")
    ap.add_argument("--terms", default=None)
    args = ap.parse_args()

    base = Path(__file__).resolve().parent
    terms_path = Path(args.terms) if args.terms else base / "sensitive_terms.json"
    text = Path(args.text_file).read_text(encoding="utf-8")
    hits = [term for term in load_terms(terms_path) if term in text]
    if hits:
        print("Blocked sensitive terms found: " + ", ".join(hits))
        raise SystemExit(2)
    print("Sensitive-term check passed")


if __name__ == "__main__":
    main()
