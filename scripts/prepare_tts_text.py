#!/usr/bin/env python3
"""Conservatively derive a TTS transcript from canonical Markdown/plain text."""
import argparse, json, re
from pathlib import Path

DIGITS = str.maketrans("0123456789", "零一二三四五六七八九")
CN_DIGITS = "零一二三四五六七八九"


def load_dict(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def cn_cardinal(n: int) -> str:
    """Chinese cardinal for the small integers used in dates/times (0..99)."""
    if not 0 <= n <= 99:
        return str(n)
    if n < 10:
        return CN_DIGITS[n]
    tens, ones = divmod(n, 10)
    if tens == 1:
        out = "十"
    else:
        out = CN_DIGITS[tens] + "十"
    if ones:
        out += CN_DIGITS[ones]
    return out


def cn_decimal(token: str) -> str:
    """Read a non-negative decimal naturally for percentages and similar speech."""
    if "." not in token:
        try:
            return cn_cardinal(int(token)) if int(token) <= 99 else token
        except ValueError:
            return token
    whole, frac = token.split(".", 1)
    try:
        whole_cn = cn_cardinal(int(whole)) if int(whole) <= 99 else whole
    except ValueError:
        return token
    return whole_cn + "点" + "".join(CN_DIGITS[int(ch)] for ch in frac)


def normalize_spoken_numbers(text: str) -> str:
    # Percentages first so 4.1% becomes 百分之四点一 rather than leaving Arabic digits.
    text = re.sub(
        r"(?<![A-Za-z0-9])([0-9]+(?:\.[0-9]+)?)\s*%",
        lambda m: "百分之" + cn_decimal(m.group(1)),
        text,
    )

    # Years are conventionally spoken digit-by-digit: 2026年 -> 二零二六年.
    text = re.sub(
        r"\b((?:19|20)\d{2})(?=\s*年)",
        lambda m: m.group(1).translate(DIGITS),
        text,
    )

    # Calendar dates: 9月5日 -> 九月五日; 10月31号 -> 十月三十一号.
    text = re.sub(
        r"(?<!\d)(\d{1,2})(?=\s*月)",
        lambda m: cn_cardinal(int(m.group(1))),
        text,
    )
    text = re.sub(
        r"(?<!\d)(\d{1,2})(?=\s*(?:日|号))",
        lambda m: cn_cardinal(int(m.group(1))),
        text,
    )

    # Clock expressions only; do not touch arbitrary model/version numbers.
    text = re.sub(
        r"(?<!\d)(\d{1,2})(?=\s*(?:点|时))",
        lambda m: cn_cardinal(int(m.group(1))),
        text,
    )
    text = re.sub(
        r"(?<!\d)(\d{1,2})(?=\s*分(?:钟)?)",
        lambda m: cn_cardinal(int(m.group(1))),
        text,
    )
    return text


def validate_spoken_text(text: str) -> None:
    bad_patterns = {
        "Arabic calendar/clock number": r"\d+(?:\.\d+)?\s*(?:年|月|日|号|点|时|分钟?)",
        "raw percent": r"\d+(?:\.\d+)?\s*%",
    }
    problems = []
    for label, pattern in bad_patterns.items():
        match = re.search(pattern, text)
        if match:
            problems.append(f"{label}: {match.group(0)!r}")
    if problems:
        raise ValueError("Unnormalized spoken text: " + "; ".join(problems))


def prepare(text, pronunciations):
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"[*_`]+", "", text)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)
    text = normalize_spoken_numbers(text)
    for src in sorted(pronunciations, key=len, reverse=True):
        text = text.replace(src, pronunciations[src])
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip() + "\n"
    validate_spoken_text(text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--dict", dest="dict_path")
    args = ap.parse_args()
    base = Path(__file__).resolve().parent
    d = Path(args.dict_path) if args.dict_path else base / "pronunciation.json"
    result = prepare(
        Path(args.input).read_text(encoding="utf-8"),
        load_dict(d),
    )
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
