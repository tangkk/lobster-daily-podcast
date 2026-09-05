#!/usr/bin/env python3
import argparse, json, os, re, xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ITUNES='http://www.itunes.com/dtds/podcast-1.0.dtd'
ATOM='http://www.w3.org/2005/Atom'

def client():
    import boto3
    from botocore.config import Config
    return boto3.client('s3',endpoint_url=os.environ['R2_ENDPOINT'].strip('"'),aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(s3={'addressing_style':'path'}))

def find_item(feed,slug):
    tree=ET.parse(feed); ch=tree.getroot().find('channel'); xs=[i for i in ch.findall('item') if (i.findtext('guid') or '')==slug]
    if len(xs)!=1: raise SystemExit(f'Expected exactly one episode for {slug}, got {len(xs)}')
    return tree,xs[0]

def object_exists(c,bucket,key):
    from botocore.exceptions import ClientError
    try: c.head_object(Bucket=bucket,Key=key); return True
    except ClientError as exc:
        code=str(exc.response.get('Error',{}).get('Code','')); status=exc.response.get('ResponseMetadata',{}).get('HTTPStatusCode')
        if code in {'404','NoSuchKey','NotFound'} or status==404: return False
        raise

def next_key(item,slug,prefix,c,bucket):
    url=item.find('enclosure').attrib['url']; name=os.path.basename(urlparse(url).path)
    if name==f'{slug}.mp3': n=2
    else:
        m=re.fullmatch(re.escape(slug)+r'-v(\d+)\.mp3',name)
        if not m: raise SystemExit(f'Unexpected enclosure filename: {name}')
        n=int(m.group(1))+1
    while object_exists(c,bucket,f"{prefix.rstrip('/')}/{slug}-v{n}.mp3"): n+=1
    return f"{prefix.rstrip('/')}/{slug}-v{n}.mp3"

def prepare(args):
    tree,item=find_item(args.feed,args.slug); enclosure=item.find('enclosure'); duration_el=item.find(f'{{{ITUNES}}}duration'); old={'url':enclosure.attrib['url'],'length':enclosure.attrib.get('length',''),'duration':duration_el.text or ''}
    c=client(); bucket=os.environ['R2_BUCKET']; public=os.environ['R2_PUBLIC_URL'].rstrip('/'); key=next_key(item,args.slug,args.prefix,c,bucket)
    c.upload_file(args.audio,bucket,key,ExtraArgs={'ContentType':'audio/mpeg'})
    enclosure.set('url',f'{public}/{key}'); enclosure.set('length',str(args.bytes)); duration_el.text=args.duration
    ET.register_namespace('itunes',ITUNES); ET.register_namespace('atom',ATOM); tree.write(args.feed,encoding='utf-8',xml_declaration=True)
    Path(args.state).write_text(json.dumps({'old':old,'new_key':key},ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'NEW_MEDIA_KEY={key}')

def rollback(args):
    state=json.loads(Path(args.state).read_text(encoding='utf-8')); tree,item=find_item(args.feed,args.slug); enc=item.find('enclosure'); dur=item.find(f'{{{ITUNES}}}duration')
    enc.set('url',state['old']['url']); enc.set('length',state['old']['length']); dur.text=state['old']['duration']; ET.register_namespace('itunes',ITUNES); ET.register_namespace('atom',ATOM); tree.write(args.feed,encoding='utf-8',xml_declaration=True)
    client().delete_object(Bucket=os.environ['R2_BUCKET'],Key=state['new_key'])

def cleanup(args):
    return

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True); q=sub.add_parser('prepare'); q.add_argument('--feed',default='feed.xml'); q.add_argument('--audio',required=True); q.add_argument('--slug',required=True); q.add_argument('--prefix',required=True); q.add_argument('--bytes',type=int,required=True); q.add_argument('--duration',required=True); q.add_argument('--state',required=True)
    for name in ('rollback','cleanup'): q=sub.add_parser(name); q.add_argument('--feed',default='feed.xml'); q.add_argument('--slug',required=True); q.add_argument('--prefix',required=True); q.add_argument('--state',required=True)
    a=p.parse_args(); {'prepare':prepare,'rollback':rollback,'cleanup':cleanup}[a.cmd](a)
if __name__=='__main__': main()
