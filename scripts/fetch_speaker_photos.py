"""
Download speaker photos from Wikipedia and save to static/speakers/<id>.jpg.

Processes speakers in descending order of speech count so the most prominent
delegates are handled first. Role-only entries (The President, The Acting
President, etc.) are skipped.

Usage:
    python scripts/fetch_speaker_photos.py [--force] [--limit N] [--dry-run]

Options:
    --force    Re-download even if the file already exists.
    --limit N  Process at most N speakers (useful for testing).
    --dry-run  Print what would be fetched without saving anything.

Wikipedia REST summary API and MediaWiki search API are used (no key
required). Requests are rate-limited to ~4/s to be polite.
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
from django.db.models import Count
from speakers.models import Speaker

PHOTOS_DIR = os.path.join(settings.BASE_DIR, 'static', 'speakers')
SUMMARY_API = 'https://en.wikipedia.org/api/rest_v1/page/summary/{}'
SEARCH_API  = 'https://en.wikipedia.org/w/api.php'
HEADERS     = {'User-Agent': 'UN-Project/1.0 (educational; github.com/un-project)'}
DELAY       = 0.25  # seconds between requests

# Speakers whose name is a role label, not a real person
ROLE_NAMES = frozenset([
    'The President',
    'The Acting President',
    'The Vice-President',
    'The Chairman',
    'The Acting Chairman',
    'The Secretary-General',
    'The Acting Secretary-General',
    'NA',
    'N/A',
    'Unknown',
])

TITLE_PREFIXES = (
    'Mr. ', 'Mrs. ', 'Ms. ', 'Miss ', 'Dr. ', 'Prof. ',
    'Sir ', 'H.E. ', 'Lord ', 'Baron ', 'Prince ', 'Princess ',
    'Ambassador ', 'Minister ',
)

# Keywords that strongly suggest the article is about a politician/diplomat
DIPLOMAT_WORDS = frozenset([
    'politician', 'diplomat', 'minister', 'ambassador', 'statesman',
    'stateswoman', 'representative', 'delegate', 'official', 'secretary',
    'chancellor', 'senator', 'member of parliament', 'envoy', 'consul',
    'foreign minister', 'prime minister', 'head of state', 'head of government',
    'attaché', 'chargé', 'un representative', 'united nations',
    'permanent representative', 'deputy permanent', 'security council',
    'general assembly', 'foreign affairs', 'ministry of foreign',
])

# Countries whose demonym does NOT contain the country name as a substring.
# e.g. "lebanese" does not contain "lebanon", so a bare `in` check would reject
# valid matches.  Add an entry here whenever the country name ≠ demonym stem.
COUNTRY_DEMONYMS = {
    'belgium':                    ['belgian'],
    'czech republic':             ['czech', 'czechoslovak'],
    'czechia':                    ['czech'],
    'denmark':                    ['danish', 'dane'],
    'finland':                    ['finnish', 'finn'],
    'france':                     ['french'],
    'germany':                    ['german'],
    'greece':                     ['greek', 'hellenic'],
    'hungary':                    ['hungarian', 'magyar'],
    'ivory coast':                ['ivorian'],
    "côte d'ivoire":              ['ivorian'],
    'ireland':                    ['irish'],
    'italy':                      ['italian'],
    'lebanon':                    ['lebanese'],
    'myanmar':                    ['burmese'],
    'netherlands':                ['dutch', 'netherlandish'],
    'norway':                     ['norwegian'],
    'palestine':                  ['palestinian'],
    'philippines':                ['filipino', 'philippine'],
    'poland':                     ['polish'],
    'portugal':                   ['portuguese'],
    'russia':                     ['russian'],
    'russian federation':         ['russian'],
    'spain':                      ['spanish'],
    'sweden':                     ['swedish'],
    'switzerland':                ['swiss'],
    'thailand':                   ['thai'],
    'turkey':                     ['turkish'],
    'türkiye':                    ['turkish'],
    'ukraine':                    ['ukrainian'],
    'united kingdom':             ['british', 'english', 'uk'],
    'united states':              ['american', 'u.s.'],
    'united states of america':   ['american', 'u.s.'],
    'china':                      ['chinese'],
    "people's republic of china": ['chinese'],
}

# Keywords that suggest the article is definitely NOT a UN diplomat
EXCLUSION_WORDS = frozenset([
    'athlete', 'footballer', 'soccer', 'basketball player', 'tennis player',
    'boxer', 'wrestler', 'cricketer', 'rugby', 'racing driver', 'swimmer',
    'sprinter', 'marathon', 'olympic', 'paralympic',
    'actor', 'actress', 'singer', 'musician', 'rapper', 'guitarist',
    'composer', 'conductor', 'violinist', 'pianist',
    'novelist', 'author', 'poet', 'screenwriter',
    'painter', 'sculptor', 'artist',
    'television presenter', 'radio presenter', 'tv presenter',
    'model', 'fashion',
    'businessman', 'entrepreneur', 'ceo', 'executive',
    'serial killer', 'criminal',
])


def strip_title(name):
    for prefix in TITLE_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def fetch_json(url, params=None):
    if params:
        url = url + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return None
    except Exception:
        return None


def fetch_summary(title):
    """Fetch Wikipedia page summary by exact title."""
    time.sleep(DELAY)
    return fetch_json(SUMMARY_API.format(urllib.parse.quote(title, safe='')))


def search_wikipedia(query, limit=5):
    """Return list of article titles matching query via MediaWiki search."""
    time.sleep(DELAY)
    data = fetch_json(SEARCH_API, {
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srlimit': limit,
        'srnamespace': 0,
        'format': 'json',
    })
    if not data:
        return []
    return [r['title'] for r in data.get('query', {}).get('search', [])]


def is_valid_diplomat(summary, country_name=None):
    """
    Return True if the Wikipedia summary is plausibly about the right diplomat.

    Checks:
    1. Must be a standard article (not disambiguation).
    2. Description or extract must contain at least one diplomat keyword.
    3. Must not contain exclusion keywords (athlete, entertainer, etc.).
    4. If country_name is supplied, at least one of description/extract must
       mention the country (or a common demonym/adjective for it).
    """
    if not summary:
        return False
    if summary.get('type') != 'standard':
        return False
    title = (summary.get('title') or '').lower()
    if 'disambiguation' in title:
        return False

    desc    = (summary.get('description') or '').lower()
    extract = (summary.get('extract')     or '').lower()[:600]
    combined = desc + ' ' + extract

    # Hard reject: clearly not a diplomat
    for word in EXCLUSION_WORDS:
        if word in combined:
            return False

    # Must have at least one positive signal
    has_diplomat_signal = any(w in combined for w in DIPLOMAT_WORDS)
    if not has_diplomat_signal:
        return False

    # Country check — if we know the country, the article should mention it
    # (using COUNTRY_DEMONYMS for countries where the name ≠ demonym stem)
    if country_name:
        country_lower = country_name.lower()
        variants = [country_lower] + COUNTRY_DEMONYMS.get(country_lower, [])
        if not any(v in combined for v in variants):
            return False

    return True


def best_thumbnail(summary):
    img = summary.get('thumbnail') or summary.get('originalimage')
    return img['source'] if img else None


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


def process_speaker(speaker, force=False, dry_run=False):
    dest = os.path.join(PHOTOS_DIR, f'{speaker.pk}.jpg')
    if os.path.exists(dest) and not force:
        return 'skipped'

    name    = strip_title(speaker.name.strip())
    country = speaker.country.name if speaker.country else None

    # ── Candidate generation ──────────────────────────────────────
    # Build a prioritised list of search queries.
    queries = [name]
    if country:
        queries += [
            f'{name} {country}',
            f'{name} {country} diplomat',
            f'{name} diplomat',
            f'{name} politician',
            f'{name} ambassador',
        ]
    else:
        queries += [f'{name} diplomat', f'{name} politician']

    # ── Try each query until we find a validated match ────────────
    # Direct title lookup only makes sense for short, natural-language names,
    # not for constructed phrases like "Salam Lebanon diplomat".
    _LOOKUP_STOP = frozenset(['diplomat', 'politician', 'ambassador'])

    seen_titles = set()
    for query in queries:
        words = query.lower().split()
        if len(words) <= 3 and not (_LOOKUP_STOP & set(words)):
            summary = fetch_summary(query)
            if summary and is_valid_diplomat(summary, country):
                img_url = best_thumbnail(summary)
                if img_url:
                    if dry_run:
                        return f'would save: {summary["title"]}'
                    if download_image(img_url, dest):
                        return f'saved ({summary["title"]})'

        # Search API — handles full-name expansion and disambiguation
        titles = search_wikipedia(query, limit=3)
        for title in titles:
            if title in seen_titles:
                continue
            seen_titles.add(title)
            summary = fetch_summary(title)
            if summary and is_valid_diplomat(summary, country):
                img_url = best_thumbnail(summary)
                if img_url:
                    if dry_run:
                        return f'would save: {summary["title"]}'
                    if download_image(img_url, dest):
                        return f'saved ({summary["title"]})'

    return 'not found'


def main():
    parser = argparse.ArgumentParser(description='Fetch speaker photos from Wikipedia.')
    parser.add_argument('--force',   action='store_true', help='Re-download existing photos.')
    parser.add_argument('--dry-run', action='store_true', help='Print matches without saving.')
    parser.add_argument('--limit',   type=int, default=None, help='Process at most N speakers.')
    args = parser.parse_args()

    os.makedirs(PHOTOS_DIR, exist_ok=True)

    # Most-prominent speakers first; skip pure role entries
    speakers = (
        Speaker.objects
        .exclude(name__in=ROLE_NAMES)
        .annotate(speech_count=Count('speeches'))
        .filter(speech_count__gt=0)
        .select_related('country')
        .order_by('-speech_count', 'name')
    )
    if args.limit:
        speakers = speakers[:args.limit]

    total     = speakers.count()
    saved     = 0
    skipped   = 0
    not_found = 0

    for i, speaker in enumerate(speakers, 1):
        result = process_speaker(speaker, force=args.force, dry_run=args.dry_run)

        if result == 'skipped':
            skipped += 1
        elif result == 'not found':
            not_found += 1
        else:
            saved += 1

        if result != 'skipped':
            print(f'[{i}/{total}] {speaker.name} ({speaker.speech_count} speeches): {result}')
        elif i % 200 == 0:
            print(f'[{i}/{total}] ... ({skipped} skipped so far)')

    label = 'Would save' if args.dry_run else 'Saved'
    print(f'\nDone. {label}: {saved}, Not found: {not_found}, Skipped: {skipped}')


if __name__ == '__main__':
    main()
