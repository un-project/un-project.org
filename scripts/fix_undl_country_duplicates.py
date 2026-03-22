"""
Fix duplicate country rows created by import_undl_votes.py before the
case-insensitive lookup fix.

The UNDL importer stored country names from DHL CSVs verbatim (e.g. 'FRANCE')
when no case-sensitive match was found, creating duplicate rows alongside the
existing properly-cased rows ('France').  populate_iso_and_flags.py then
assigned iso3 codes to the new duplicates, leaving the canonical rows with data
but no iso3.

This script:
  1. Finds all country rows that have an iso3 but no linked speakers.
  2. Looks for a case-insensitive match that has speakers (or more data).
  3. Reassigns the iso3 (and country_votes) from the dead row to the canonical
     row, then deletes the dead row.

Usage:
    python scripts/fix_undl_country_duplicates.py [--dry-run]
"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'un_site.settings')

import django
django.setup()

from django.db import transaction
from countries.models import Country
from speakers.models import Speaker
from votes.models import CountryVote


def run(dry_run=False):
    # Countries that have iso3 but no speakers — candidate duplicates
    dead = [
        c for c in Country.objects.filter(iso3__isnull=False)
        if not Speaker.objects.filter(country=c).exists()
    ]
    print(f"Found {len(dead)} iso3-bearing countries with no speakers.")

    fixed = 0
    for orphan in dead:
        # Find a canonical row: same name (case-insensitive), different pk
        canonical = (
            Country.objects
            .filter(name__iexact=orphan.name)
            .exclude(pk=orphan.pk)
            .first()
        )
        if canonical is None:
            continue

        print(f"  MERGE {orphan.name!r} (pk={orphan.pk}, iso3={orphan.iso3})"
              f" → {canonical.name!r} (pk={canonical.pk})")

        if not dry_run:
            with transaction.atomic():
                # Move country_votes: delete dupes, reassign the rest
                orphan_vote_ids = set(
                    CountryVote.objects.filter(country=orphan)
                    .values_list('vote_id', flat=True)
                )
                canonical_vote_ids = set(
                    CountryVote.objects.filter(country=canonical)
                    .values_list('vote_id', flat=True)
                )
                dupe_ids   = orphan_vote_ids & canonical_vote_ids
                unique_ids = orphan_vote_ids - canonical_vote_ids
                if dupe_ids:
                    CountryVote.objects.filter(
                        country=orphan, vote_id__in=dupe_ids
                    ).delete()
                if unique_ids:
                    CountryVote.objects.filter(
                        country=orphan, vote_id__in=unique_ids
                    ).update(country_id=canonical.pk)

                # Clear iso codes from orphan first to avoid unique conflicts
                orphan_iso3 = orphan.iso3
                orphan_iso2 = orphan.iso2
                Country.objects.filter(pk=orphan.pk).update(iso3=None, iso2=None)
                Country.objects.filter(pk=orphan.pk).delete()

                # Assign iso3 (and iso2) to canonical if not already set
                updates = {}
                if not canonical.iso3 and orphan_iso3:
                    updates['iso3'] = orphan_iso3
                if not canonical.iso2 and orphan_iso2:
                    updates['iso2'] = orphan_iso2
                if updates:
                    Country.objects.filter(pk=canonical.pk).update(**updates)

        fixed += 1

    action = "Would fix" if dry_run else "Fixed"
    print(f"\n{action} {fixed} duplicate country rows.")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    run(dry_run=args.dry_run)
