#!/usr/bin/env python3
"""Build the RSS episode title from a date and an optional one-line headline.

Weekday:  龙虾日报｜10月27日：<headline>
Sunday:   龙虾日报｜周回顾 10月25日：<headline>
Falls back to the date-only title when the headline is missing or unusable.
"""
import datetime as dt
import re
import sys
from pathlib import Path

MAX_HEADLINE = 40


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
    label = f"周回顾 {d.month}月{d.day}日" if d.isoweekday() == 7 else f"{d.month}月{d.day}日"
    return f"龙虾日报｜{label}：{h}"


if __name__ == "__main__":
    date = sys.argv[1]
    text = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 and Path(sys.argv[2]).exists() else ""
    print(build(date, text))
