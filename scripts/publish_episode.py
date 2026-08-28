#!/usr/bin/env python3
import argparse, datetime as dt, os, xml.etree.ElementTree as ET
from email.utils import format_datetime
def ensure_namespaces():
    ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd'); ET.register_namespace('atom','http://www.w3.org/2005/Atom')
def r2_client(endpoint):
    import boto3
    from botocore.config import Config
    return boto3.client('s3',endpoint_url=endpoint,aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(s3={'addressing_style':'path'}))
def ensure_key_absent(c,bucket,key):
    try: c.head_object(Bucket=bucket,Key=key)
    except Exception as exc:
        r=getattr(exc,'response',{}) or {}; code=str(r.get('Error',{}).get('Code','')); status=r.get('ResponseMetadata',{}).get('HTTPStatusCode')
        if code in {'404','NoSuchKey','NotFound'} or status==404: return
        raise
    raise SystemExit(f'R2 object already exists: {key}')
def add_episode(feed,enclosure_url,size,slug,title,description,duration):
    tree=ET.parse(feed); ch=tree.getroot().find('channel'); item=ET.Element('item'); ET.SubElement(item,'title').text=title; ET.SubElement(item,'description').text=description; ET.SubElement(item,'pubDate').text=format_datetime(dt.datetime.now(dt.timezone.utc)); ET.SubElement(item,'guid',{'isPermaLink':'false'}).text=slug; ET.SubElement(item,'enclosure',{'url':enclosure_url,'length':str(size),'type':'audio/mpeg'}); ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text=duration; ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text='false'; first=ch.find('item'); ch.insert(list(ch).index(first),item) if first is not None else ch.append(item); tree.write(feed,encoding='utf-8',xml_declaration=True)
def main():
    ensure_namespaces(); p=argparse.ArgumentParser(); p.add_argument('--feed',default='feed.xml'); p.add_argument('--audio',required=True); p.add_argument('--slug',required=True); p.add_argument('--title',required=True); p.add_argument('--description',required=True); p.add_argument('--duration',required=True); p.add_argument('--prefix',required=True); a=p.parse_args(); endpoint=os.environ['R2_ENDPOINT'].strip('"'); bucket=os.environ['R2_BUCKET']; public=os.environ['R2_PUBLIC_URL'].rstrip('/'); key=f"{a.prefix.rstrip('/')}/{a.slug}.mp3"; c=r2_client(endpoint); ensure_key_absent(c,bucket,key); size=os.path.getsize(a.audio); c.upload_file(a.audio,bucket,key,ExtraArgs={'ContentType':'audio/mpeg'}); add_episode(a.feed,f'{public}/{key}',size,a.slug,a.title,a.description,a.duration)
if __name__=='__main__': main()
