#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import re
import xml.etree.ElementTree as ET
from email.utils import format_datetime
from urllib.parse import urlparse

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"


def ensure_namespaces():
    ET.register_namespace("itunes", ITUNES)
    ET.register_namespace("atom", ATOM)


def r2_client(endpoint):
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(s3={"addressing_style": "path"}),
    )


def set_text(parent, tag, text, attrs=None):
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag, attrs or {})
    elif attrs:
        node.attrib.clear()
        node.attrib.update(attrs)
    node.text = text
    return node


def existing_episode(feed, slug):
    tree = ET.parse(feed)
    channel = tree.getroot().find("channel")
    if channel is None:
        raise SystemExit("RSS channel missing")
    matches = [i for i in channel.findall("item") if i.findtext("guid") == slug]
    if len(matches) > 1:
        raise SystemExit(f"Duplicate RSS GUID already present: {slug}")
    return matches[0] if matches else None


def object_exists(client, bucket, key):
    from botocore.exceptions import ClientError

    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code in {"404", "NoSuchKey", "NotFound"} or status == 404:
            return False
        raise


def next_media_key(feed, slug, prefix, client, bucket):
    """Choose the production media key.

    First publication uses <slug>.mp3. Any later publication of the same stable
    GUID is a rework and MUST use a fresh versioned enclosure key (-v2, -v3, ...).
    Existing version keys are skipped so a rework never overwrites historical bytes.
    """
    prefix = prefix.rstrip("/")
    item = existing_episode(feed, slug)
    if item is None:
        return f"{prefix}/{slug}.mp3", False

    enclosure = item.find("enclosure")
    if enclosure is None or not enclosure.attrib.get("url"):
        raise SystemExit(f"Existing episode has no enclosure URL: {slug}")

    current_name = os.path.basename(urlparse(enclosure.attrib["url"]).path)
    base_name = f"{slug}.mp3"
    version_match = re.fullmatch(re.escape(slug) + r"-v(\d+)\.mp3", current_name)
    if current_name == base_name:
        next_version = 2
    elif version_match:
        next_version = int(version_match.group(1)) + 1
    else:
        raise SystemExit(f"Unexpected enclosure filename for {slug}: {current_name}")

    while True:
        key = f"{prefix}/{slug}-v{next_version}.mp3"
        if not object_exists(client, bucket, key):
            return key, True
        next_version += 1


def upsert_episode(feed, enclosure_url, size, slug, title, description, duration):
    tree = ET.parse(feed)
    channel = tree.getroot().find("channel")
    if channel is None:
        raise SystemExit("RSS channel missing")

    matches = [i for i in channel.findall("item") if i.findtext("guid") == slug]
    if len(matches) > 1:
        raise SystemExit(f"Duplicate RSS GUID already present: {slug}")

    now = dt.datetime.now(dt.timezone.utc)
    if matches:
        item = matches[0]
    else:
        item = ET.Element("item")
        first = channel.find("item")
        if first is None:
            channel.append(item)
        else:
            channel.insert(list(channel).index(first), item)
        set_text(item, "pubDate", format_datetime(now))

    set_text(item, "title", title)
    set_text(item, "description", description)
    if item.find("pubDate") is None:
        set_text(item, "pubDate", format_datetime(now))
    set_text(item, "guid", slug, {"isPermaLink": "false"})
    set_text(
        item,
        "enclosure",
        None,
        {"url": enclosure_url, "length": str(size), "type": "audio/mpeg"},
    )
    set_text(item, f"{{{ITUNES}}}duration", duration)
    set_text(item, f"{{{ITUNES}}}episodeType", "full")
    set_text(item, f"{{{ITUNES}}}explicit", "false")
    set_text(channel, "lastBuildDate", format_datetime(now))

    tree.write(feed, encoding="utf-8", xml_declaration=True)


def main():
    ensure_namespaces()
    p = argparse.ArgumentParser()
    p.add_argument("--feed", default="feed.xml")
    p.add_argument("--audio", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--duration", required=True)
    p.add_argument("--prefix", required=True)
    a = p.parse_args()

    endpoint = os.environ["R2_ENDPOINT"].strip('"')
    bucket = os.environ["R2_BUCKET"]
    public = os.environ["R2_PUBLIC_URL"].rstrip("/")
    client = r2_client(endpoint)
    size = os.path.getsize(a.audio)

    key, is_rework = next_media_key(a.feed, a.slug, a.prefix, client, bucket)
    enclosure_url = f"{public}/{key}"
    client.upload_file(a.audio, bucket, key, ExtraArgs={"ContentType": "audio/mpeg"})
    upsert_episode(a.feed, enclosure_url, size, a.slug, a.title, a.description, a.duration)

    print(f"REWORK={'1' if is_rework else '0'}")
    print(f"MEDIA_KEY={key}")
    print(enclosure_url)


if __name__ == "__main__":
    main()
