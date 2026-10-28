#!/usr/bin/env python3
"""Build the RSS episode title from a date and an optional one-line headline.

Weekday:  10.28｜<headline>｜压力指数 83
Sunday:   周回顾 10.25｜<headline>｜压力指数 83
The 压力指数 segment appears only when a stress reading file is given.
Falls back to the date-only title when the headline is missing or unusable.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

MAX_HEADLINE = 72  # hard safety cap in raw characters; editorial target is ~40 CJK-width


def clean(headline: str) -> str:
    line = headline.strip().splitlines()[0] if headline.strip() else ""
    line = re.sub(r'["$`\\\\<>]', "", line)
    line = re.sub(r"\s+", " ", line).strip(" ：:|｜")
    return line[:MAX_HEADLINE].rstrip()


def stress_label(path) -> str:
    try:
        value = float(json.loads(Path(path).read_text(encoding="utf-8"))["index"])
    except Exception:
        return ""
    return f"压力指数 {value:.0f}" if 0 <= value <= 100 else ""


def build(date: str, headline: str, stress: str = "", weekly=None) -> str:
    d = dt.date.fromisoformat(date)
    fallback = f"龙虾日报｜{d:%Y}年{d:%m}月{d:%d}日"
    h = clean(headline)
    if not h:
        return fallback
    stamp = f"{d.month}.{d.day:02d}"
    if weekly is None:
        weekly = d.isoweekday() == 7
    label = f"周回顾 {stamp}" if weekly else stamp
    return f"{label}｜{h}｜{stress}" if stress else f"{label}｜{h}"


if __name__ == "__main__":
    date = sys.argv[1]
    text = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 and Path(sys.argv[2]).exists() else ""
    stress = stress_label(sys.argv[3]) if len(sys.argv) > 3 and Path(sys.argv[3]).exists() else ""
    print(build(date, text, stress))
