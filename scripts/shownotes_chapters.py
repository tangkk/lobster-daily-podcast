#!/usr/bin/env python3
"""Insert timestamped chapters into episode shownotes.

Reads the segment timeline written by xfyun_segmented_run.py (start seconds and
paragraph index per TTS segment), labels each paragraph from its opening words,
and inserts a "章节" block before the 文字版 line. Any problem returns the
description unchanged so publication is never blocked.
"""
import argparse
import json
import re
import sys
from pathlib import Path

MAX_CHAPTERS = 15
MAX_LABEL = 14
FIXED_LABELS = [
    (r"^今日数字", "今日数字"),
    (r"^本周数字", "本周数字"),
    (r"^概念小课堂", "概念小课堂"),
    (r"^被忽视的信号", "被忽视的信号"),
    (r"^我们的判断", "我们的判断"),
    (r"^(今天|本周|下周|接下来)(重点)?(关注|要关注|值得关注)", "接下来关注"),
    (r"^如果你希望我们", "听众留言"),
]


def stamp(seconds: float) -> str:
    s = max(0, int(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def label_for(text: str) -> str:
    t = text.strip()
    for pattern, label in FIXED_LABELS:
        if re.match(pattern, t):
            return label
    clause = re.split(r"[，。：；！？,:;]", t, maxsplit=1)[0]
    clause = re.sub(r"^(先看|再看|最后看|最后|另外|此外|同时)", "", clause)
    clause = re.sub(r"方面$", "", clause).strip()
    if not clause:
        return ""
    return clause if len(clause) <= MAX_LABEL else clause[:MAX_LABEL] + "…"


def build_chapters(timeline, sunday=False):
    first_by_para = {}
    for seg in timeline:
        first_by_para.setdefault(seg["para"], seg)
    chapters = []
    summary_done = False
    for para in sorted(first_by_para):
        seg = first_by_para[para]
        text = seg["text"]
        opening = re.match(r"^\s*龙虾日报，", text)
        if opening:
            rest = re.sub(r"^\s*龙虾日报，[^。]*。\s*", "", text)
            rest = re.sub(r"^\s*周日这期，我们总结本周的状态。\s*", "", rest)
            if not rest.strip():
                continue  # bare opening line; the summary chapter starts at 00:00
        if not summary_done:
            chapters.append((0.0, "本周概要" if sunday else "今日概要"))
            summary_done = True
            continue
        label = label_for(text)
        if label and label != chapters[-1][1]:
            chapters.append((seg["start"], label))
    return chapters[:MAX_CHAPTERS]


def insert_chapters(description: str, chapters) -> str:
    if len(chapters) < 3:
        return description
    block = "章节\n" + "\n".join(f"{stamp(t)} {label}" for t, label in chapters)
    marker = "\n文字版："
    if marker in description:
        head, tail = description.split(marker, 1)
        return head.rstrip() + "\n\n" + block + "\n" + marker + tail
    return description.rstrip() + "\n\n" + block


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--description-file", required=True)
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--sunday", action="store_true")
    a = ap.parse_args()
    description = Path(a.description_file).read_text(encoding="utf-8").strip()
    try:
        timeline = json.loads(Path(a.timeline).read_text(encoding="utf-8"))
        description = insert_chapters(description, build_chapters(timeline, a.sunday))
    except Exception as exc:  # never block publication
        print(f"Chapters skipped: {exc}", file=sys.stderr)
    print(description)


if __name__ == "__main__":
    main()
