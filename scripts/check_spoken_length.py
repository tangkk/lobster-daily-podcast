#!/usr/bin/env python3
"""Fail closed on an under-length new Daily Brief or Weekly Review spoken script.

Counts Chinese ideographs in the canonical source, not bytes, punctuation, or
post-normalization TTS text. Existing published episodes are grandfathered.
"""
import argparse
import datetime as dt
import pathlib
import re
import sys

HAN = re.compile(r"[\u3400-\u9fff]")
LIMITS = {"daily": 1300, "weekly": 1800}


def count_han(text: str) -> int:
    return len(HAN.findall(text))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="Asia/Shanghai edition date YYYY-MM-DD")
    p.add_argument("--file", required=True)
    args = p.parse_args()
    edition = dt.date.fromisoformat(args.date)
    kind = "weekly" if edition.weekday() == 6 else "daily"
    minimum = LIMITS[kind]
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    count = count_han(text)
    print(f"spoken_length: edition={args.date} kind={kind} han_characters={count} minimum={minimum}")
    if count < minimum:
        print(
            f"ERROR: spoken script short by {minimum - count} Chinese characters; "
            "add sourced context, comparisons and causal explanation, not filler. "
            "Keep the handoff staged and do not publish.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
