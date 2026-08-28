#!/usr/bin/env python3
"""Conservatively derive a TTS transcript from canonical Markdown/plain text."""
import argparse, json, re
from pathlib import Path
DIGITS = str.maketrans("0123456789", "零一二三四五六七八九")
def load_dict(path):
    if not path.exists(): return {}
    return json.loads(path.read_text(encoding="utf-8"))
def prepare(text, pronunciations):
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"[*_`]+", "", text)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"百分之\1", text)
    text = re.sub(r"\b((?:19|20)\d{2})(?=\s*年)", lambda m: m.group(1).translate(DIGITS), text)
    for src in sorted(pronunciations, key=len, reverse=True): text = text.replace(src, pronunciations[src])
    text = re.sub(r"[ \t]+", " ", text); text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("-o","--output"); ap.add_argument("--dict",dest="dict_path"); args=ap.parse_args(); base=Path(__file__).resolve().parent; d=Path(args.dict_path) if args.dict_path else base/"pronunciation.json"; result=prepare(Path(args.input).read_text(encoding="utf-8"),load_dict(d)); Path(args.output).write_text(result,encoding="utf-8") if args.output else print(result,end="")
if __name__=="__main__": main()
