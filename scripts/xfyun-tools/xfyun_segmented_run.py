#!/usr/bin/env python3
import argparse, os, re, subprocess, tempfile
from xfyun_super_official_run import load_profile, run_once
SENTENCE=re.compile(r'(?<=[。！？!?])')
def split_text(text,target_min=240,target_max=420):
    out=[]
    for p in [p.strip() for p in re.split(r'\n\s*\n+',text.strip()) if p.strip()]:
        if len(p)<=target_max: out.append(p); continue
        buf=''
        for s in [s.strip() for s in SENTENCE.split(p) if s.strip()]:
            if buf and len(buf)+len(s)>target_max: out.append(buf); buf=s
            else: buf+=s
        if buf: out.append(buf)
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--text-file',required=True); ap.add_argument('--out',required=True); ap.add_argument('--profile',default='default'); ap.add_argument('--pause-ms',type=int,default=350); ap.add_argument('--min-chars',type=int,default=240); ap.add_argument('--max-chars',type=int,default=420); ap.add_argument('--url',default='wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6'); a=ap.parse_args(); text=open(a.text_file,encoding='utf-8').read().strip(); segs=split_text(text,a.min_chars,a.max_chars); p=load_profile(a.profile); voice=p.get('voice','x6_lingyuyan_pro'); speed=p.get('speed',50); volume=p.get('volume',52); pitch=p.get('pitch',50)
    with tempfile.TemporaryDirectory() as d:
        parts=[]
        for i,s in enumerate(segs): path=os.path.join(d,f'{i:03d}.mp3'); run_once(a.url,path,voice,s,speed,volume,pitch); parts.append(path)
        silence=os.path.join(d,'silence.mp3'); subprocess.run(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=24000:cl=mono','-t',str(a.pause_ms/1000),'-q:a','9',silence],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); concat=os.path.join(d,'concat.txt'); f=open(concat,'w'); [f.write(f"file '{p}'\n"+(f"file '{silence}'\n" if i<len(parts)-1 else '')) for i,p in enumerate(parts)]; f.close(); subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat,'-c:a','libmp3lame','-ar','24000','-ac','1',a.out],check=True)
if __name__=='__main__': main()
