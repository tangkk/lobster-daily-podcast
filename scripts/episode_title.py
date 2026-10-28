#!/usr/bin/env python3
"""Build the RSS episode title from a date and an optional one-line headline.

Weekday:  10.28｜<headline>
Sunday:   周回顾 10.25｜<headline>
Falls back to the date-only title when the headline is missing or unusable.
"""
import datetime as dt
import re
import sys
from pathlib import Path

MAX_HEADLINE = 48


def clean(headline: str) -> str:
    line = headline.strip().splitlines()[0] if headline.strip() else ""
    line = re.sub(r'["$`\\\\<>]', "", line)
    line = re.sub(r"\s+", " ", line).strip(" ：:|｜")
    return line[:MAX_HEADLINE].rstrip()


def build(date: str, headline: str) -> str:
    d = dt.date.fromisoformat(date)
    fallback = f"龙虾日报｜{d:%Y}年{d:%m}月{d:%d}日"
    h = clean(headline)
    if not h:
        return fallback
    stamp = f"{d.month}.{d.day:02d}"
    label = f"周回顾 {stamp}" if d.isoweekday() == 7 else stamp
    return f"{label}｜{h}"


if __name__ == "__main__":
    date = sys.argv[1]
    text = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 and Path(sys.argv[2]).exists() else ""
    print(build(date, text))
