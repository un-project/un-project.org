"""
Download speaker photos from Wikipedia and save to static/speakers/<id>.jpg.

Usage:
    python scripts/fetch_speaker_photos.py [--force] [--limit N]

Options:
    --force   Re-download even if the file already exists.
    --limit N Process at most N speakers (useful for testing).

Wikipedia REST API is used (no API key required). Requests are rate-limited
to ~5/s to be polite. Only speakers whose Wikipedia page includes a thumbnail
image will get a photo saved.
"""
import os
import sys
import time
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'un_site.settings')

import django
django.setup()

from django.conf import settings
from speakers.models import Speaker

PHOTOS_DIR = os.path.join(settings.BASE_DIR, 'static', 'speakers')
SUMMARY_API = 'https://en.wikipedia.org/api/rest_v1/page/summary/{}'
HEADERS = {'User-Agent': 'UN-Project/1.0 (educational; contact via github)'}
DELAY = 0.25  # seconds between requests


def fetch_summary(title):
    url = SUMMARY_API.format(urllib.parse.quote(title, safe=''))
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None


def download_image(url, dest_path):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(dest_path, 'wb') as f:
            f.write(data)
        return True
    except Exception:
        return False


TITLE_PREFIXES = ('Mr. ', 'Mrs. ', 'Ms. ', 'Dr. ', 'Prof. ', 'Sir ', 'H.E. ', 'Lord ')


def strip_title(name):
    for prefix in TITLE_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def candidate_titles(speaker):
    """Generate Wikipedia article title candidates for a speaker."""
    raw = speaker.name.strip()
    name = strip_title(raw)
    yield name
    if name != raw:
        yield raw  # also try with prefix, occasionally used
    # Try with country context for common diplomatic roles
    if speaker.country:
        country = speaker.country.name
        yield f"{name} (diplomat)"
        yield f"{name} (politician)"
        yield f"{name} ({country} politician)"


def process_speaker(speaker, force=False):
    dest = os.path.join(PHOTOS_DIR, f'{speaker.pk}.jpg')
    if os.path.exists(dest) and not force:
        return 'skipped'

    for title in candidate_titles(speaker):
        time.sleep(DELAY)
        data = fetch_summary(title)
        if not data:
            continue
        # Confirm the page is about a person (not a disambiguation or place)
        if data.get('type') not in ('standard', 'disambiguation'):
            continue
        thumbnail = data.get('thumbnail') or data.get('originalimage')
        if not thumbnail:
            continue
        img_url = thumbnail['source']
        # Convert to JPEG-compatible URL — Wikipedia serves .jpg for most portraits
        if download_image(img_url, dest):
            return f'saved ({title})'

    return 'not found'


def main():
    parser = argparse.ArgumentParser(description='Fetch speaker photos from Wikipedia.')
    parser.add_argument('--force', action='store_true', help='Re-download existing photos.')
    parser.add_argument('--limit', type=int, default=None, help='Process at most N speakers.')
    args = parser.parse_args()

    os.makedirs(PHOTOS_DIR, exist_ok=True)

    speakers = Speaker.objects.select_related('country').order_by('name')
    if args.limit:
        speakers = speakers[:args.limit]

    total = speakers.count()
    saved = skipped = not_found = 0

    for i, speaker in enumerate(speakers, 1):
        result = process_speaker(speaker, force=args.force)
        if result == 'skipped':
            skipped += 1
        elif result == 'not found':
            not_found += 1
        else:
            saved += 1

        if result != 'skipped':
            status = f'[{i}/{total}] {speaker.name}: {result}'
            print(status)
        elif i % 100 == 0:
            print(f'[{i}/{total}] ... ({skipped} skipped so far)')

    print(f'\nDone. Saved: {saved}, Not found: {not_found}, Skipped (already existed): {skipped}')


if __name__ == '__main__':
    main()
