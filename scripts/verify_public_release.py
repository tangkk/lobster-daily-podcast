#!/usr/bin/env python3
import argparse
import os
import subprocess
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET

ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'


def download(url, path):
    req = urllib.request.Request(url, headers={'User-Agent':'lobster-podcast-release-verifier','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req, timeout=30) as r, open(path, 'wb') as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk: break
            f.write(chunk)


def verify_audio(url, expected_bytes, expected_duration):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'episode.mp3')
        download(url + ('&' if '?' in url else '?') + f'verify={int(time.time())}', path)
        actual = os.path.getsize(path)
        if actual != expected_bytes:
            raise RuntimeError(f'public MP3 size mismatch: expected {expected_bytes}, got {actual}')
        seconds = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',path], text=True).strip())
        rounded = round(seconds)
        actual_duration = f'{rounded//3600:02d}:{(rounded%3600)//60:02d}:{rounded%60:02d}'
        if actual_duration != expected_duration:
            raise RuntimeError(f'public MP3 duration mismatch: expected {expected_duration}, got {actual_duration}')


def verify_feed(repo, slug, expected_url, expected_bytes, expected_duration):
    feed_url = f'https://raw.githubusercontent.com/{repo}/main/feed.xml'
    last = None
    for attempt in range(30):
        try:
            req = urllib.request.Request(feed_url + f'?verify={int(time.time())}-{attempt}', headers={'User-Agent':'lobster-podcast-release-verifier','Cache-Control':'no-cache'})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            ch = ET.fromstring(data).find('channel')
            items = [i for i in ch.findall('item') if (i.findtext('guid') or '') == slug]
            if len(items) != 1:
                raise RuntimeError(f'expected exactly one live RSS item for {slug}, got {len(items)}')
            item = items[0]
            enclosure = item.find('enclosure')
            if enclosure is None: raise RuntimeError('live RSS item has no enclosure')
            if enclosure.attrib.get('url') != expected_url: raise RuntimeError('live RSS enclosure URL mismatch')
            if int(enclosure.attrib.get('length','-1')) != expected_bytes: raise RuntimeError('live RSS enclosure length mismatch')
            duration = item.findtext(f'{{{ITUNES}}}duration')
            if duration != expected_duration: raise RuntimeError(f'live RSS duration mismatch: {duration}')
            return
        except Exception as exc:
            last = exc
            time.sleep(4)
    raise RuntimeError(f'live RSS verification failed: {last}')


def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo',required=True); p.add_argument('--slug',required=True); p.add_argument('--url',required=True); p.add_argument('--bytes',type=int,required=True); p.add_argument('--duration',required=True); a=p.parse_args()
    verify_audio(a.url,a.bytes,a.duration)
    verify_feed(a.repo,a.slug,a.url,a.bytes,a.duration)
    print(f'PUBLIC RELEASE VERIFIED: {a.slug}')

if __name__=='__main__': main()
