#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path


def load_terms(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [str(x) for x in data.get("blocked_terms", []) if str(x)]


def contains_term(text: str, terms):
    return any(term in text for term in terms)


def filter_text(text: str, terms):
    """Remove complete sentences containing blocked terms; drop whole paragraph only if needed.

    This intentionally preserves surrounding factual content and avoids leaving a sentence
    with a sensitive token simply blanked out in the middle.
    """
    removed = []
    out_paragraphs = []
    # Keep paragraph structure, but filter at sentence granularity first.
    for paragraph in re.split(r"\n\s*\n+", text.strip()):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # Sentence chunks retain terminal punctuation when present.
        chunks = [m.group(0).strip() for m in re.finditer(r"[^。！？!?；;]+[。！？!?；;]?", paragraph) if m.group(0).strip()]
        kept = []
        for chunk in chunks:
            hits = [term for term in terms if term in chunk]
            if hits:
                removed.append({"text": chunk, "terms": hits})
            else:
                kept.append(chunk)
        cleaned = "".join(kept).strip()
        # Defensive fallback for unusual punctuation/tokenization.
        if cleaned and contains_term(cleaned, terms):
            hits = [term for term in terms if term in cleaned]
            removed.append({"text": paragraph, "terms": hits})
            cleaned = ""
        if cleaned:
            out_paragraphs.append(cleaned)
    result = "\n\n".join(out_paragraphs).strip()
    return result, removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text_file")
    ap.add_argument("--terms", default=None)
    ap.add_argument("--filter-output", default=None,
                    help="Write a filtered copy with sensitive sentences removed instead of failing")
    args = ap.parse_args()

    base = Path(__file__).resolve().parent
    terms_path = Path(args.terms) if args.terms else base / "sensitive_terms.json"
    text = Path(args.text_file).read_text(encoding="utf-8")
    terms = load_terms(terms_path)

    if args.filter_output:
        filtered, removed = filter_text(text, terms)
        if not filtered:
            print("Sensitive-term filter removed all spoken content")
            raise SystemExit(2)
        Path(args.filter_output).write_text(filtered + "\n", encoding="utf-8")
        if removed:
            unique_terms = sorted({t for item in removed for t in item["terms"]})
            print(f"Sensitive-term filter removed {len(removed)} sentence(s); matched {len(unique_terms)} configured term(s)")
        else:
            print("Sensitive-term filter: no removals needed")
        return

    hits = [term for term in terms if term in text]
    if hits:
        print(f"Sensitive terms remain after filtering: {len(hits)} configured term(s) matched")
        raise SystemExit(2)
    print("Sensitive-term check passed")


if __name__ == "__main__":
    main()
