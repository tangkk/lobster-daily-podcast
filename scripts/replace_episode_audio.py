#!/usr/bin/env python3
import argparse, os, xml.etree.ElementTree as ET
from pathlib import Path
def client():
    import boto3
    from botocore.config import Config
    return boto3.client('s3',endpoint_url=os.environ['R2_ENDPOINT'].strip('"'),aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(s3={'addressing_style':'path'}))
def find_item(feed,slug):
    tree=ET.parse(feed); ch=tree.getroot().find('channel')
    for item in ch.findall('item'):
        if (item.findtext('guid') or '')==slug: return tree,item
    raise SystemExit(f'Episode does not exist: {slug}')
def prepare(args):
    tree,item=find_item(args.feed,args.slug); enclosure=item.find('enclosure'); duration_el=item.find('{http://www.itunes.com/dtds/podcast-1.0.dtd}duration'); key=f"{args.prefix.rstrip('/')}/{args.slug}.mp3"; c=client(); backup_key=f"_replacement_backups/{args.slug}/{os.environ.get('GITHUB_SHA','manual')}.mp3"; c.copy_object(Bucket=os.environ['R2_BUCKET'],Key=backup_key,CopySource={'Bucket':os.environ['R2_BUCKET'],'Key':key},ContentType='audio/mpeg',MetadataDirective='REPLACE'); c.upload_file(args.audio,os.environ['R2_BUCKET'],key,ExtraArgs={'ContentType':'audio/mpeg'}); enclosure.set('length',str(args.bytes)); duration_el.text=args.duration; ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd'); ET.register_namespace('atom','http://www.w3.org/2005/Atom'); tree.write(args.feed,encoding='utf-8',xml_declaration=True); Path(args.state).write_text(backup_key+'\n')
def rollback(args):
    backup_key=Path(args.state).read_text().strip(); key=f"{args.prefix.rstrip('/')}/{args.slug}.mp3"; c=client(); c.copy_object(Bucket=os.environ['R2_BUCKET'],Key=key,CopySource={'Bucket':os.environ['R2_BUCKET'],'Key':backup_key},ContentType='audio/mpeg',MetadataDirective='REPLACE'); c.delete_object(Bucket=os.environ['R2_BUCKET'],Key=backup_key)
def cleanup(args): client().delete_object(Bucket=os.environ['R2_BUCKET'],Key=Path(args.state).read_text().strip())
def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True); q=sub.add_parser('prepare'); q.add_argument('--feed',default='feed.xml'); q.add_argument('--audio',required=True); q.add_argument('--slug',required=True); q.add_argument('--prefix',required=True); q.add_argument('--bytes',type=int,required=True); q.add_argument('--duration',required=True); q.add_argument('--state',required=True)
    for name in ('rollback','cleanup'): q=sub.add_parser(name); q.add_argument('--slug',required=True); q.add_argument('--prefix',required=True); q.add_argument('--state',required=True)
    a=p.parse_args(); {'prepare':prepare,'rollback':rollback,'cleanup':cleanup}[a.cmd](a)
if __name__=='__main__': main()
