#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import xml.etree.ElementTree as ET
from email.utils import format_datetime

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


def backup_existing_object(client, bucket, key, slug):
    """Back up the current production object before any overwrite.

    No backup is created for a first publish where the canonical object does not yet exist.
    The backup key is unique per GitHub run when available, otherwise per UTC timestamp.
    """
    from botocore.exceptions import ClientError

    try:
        client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code in {"404", "NoSuchKey", "NotFound"} or status == 404:
            return None
        raise

    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "").strip()
    if run_id:
        version = f"run-{run_id}" + (f"-attempt-{attempt}" if attempt else "")
    else:
        version = "utc-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    backup_key = f"_release_backups/{slug}/{version}.mp3"
    client.copy_object(
        Bucket=bucket,
        Key=backup_key,
        CopySource={"Bucket": bucket, "Key": key},
        ContentType="audio/mpeg",
        MetadataDirective="REPLACE",
    )
    print(f"BACKUP_CREATED={backup_key}")
    return backup_key


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
    key = f"{a.prefix.rstrip('/')}/{a.slug}.mp3"
    enclosure_url = f"{public}/{key}"

    client = r2_client(endpoint)
    size = os.path.getsize(a.audio)

    # Same date/slug remains intentionally replaceable, but every overwrite is now recoverable.
    backup_existing_object(client, bucket, key, a.slug)
    client.upload_file(a.audio, bucket, key, ExtraArgs={"ContentType": "audio/mpeg"})
    upsert_episode(a.feed, enclosure_url, size, a.slug, a.title, a.description, a.duration)
    print(enclosure_url)


if __name__ == "__main__":
    main()
