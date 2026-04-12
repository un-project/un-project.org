"""
Clean the countries table: remove garbage OCR rows, fix misspellings,
and reassign FK data (speakers, votes, sponsors) to canonical country rows.

Strategy:
  1. For each non-iso3 row, attempt to map it to a canonical iso3 via
     OVERRIDES (exact) or pycountry (exact name/common/official).
  2. If matched: reassign speakers / country_votes / resolution_sponsors to
     the canonical row (skipping duplicates), then delete the variant row.
  3. If not matched: nullify speaker.country_id, delete country_votes and
     resolution_sponsors, then delete the row.

Usage:
    python scripts/clean_countries.py [--dry-run]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'un_site.settings')

import django
django.setup()

import pycountry
from django.db import connection, transaction

dry_run = '--dry-run' in sys.argv

# Import the overrides from the populate script so we stay in sync.
from scripts.populate_iso_and_flags import OVERRIDES


def _canonical_iso3(name: str):
    """Return iso3 for a name using OVERRIDES then pycountry exact matches."""
    if name in OVERRIDES:
        return OVERRIDES[name]
    for getter in (
        lambda n: pycountry.countries.get(name=n),
        lambda n: pycountry.countries.get(common_name=n),
        lambda n: pycountry.countries.get(official_name=n),
        lambda n: pycountry.historic_countries.get(name=n),
    ):
        c = getter(name)
        if c:
            return c.alpha_3
    return None


def main():
    with connection.cursor() as cur:
        # Fetch all non-iso3 country rows.
        cur.execute("SELECT id, name FROM countries WHERE iso3 IS NULL ORDER BY name")
        bad_rows = cur.fetchall()

    print(f"Non-iso3 rows to process: {len(bad_rows)}\n")

    reassigned = 0
    orphaned   = 0
    deleted    = 0
    errors     = []

    with transaction.atomic():
        for country_id, name in bad_rows:
            iso3 = _canonical_iso3(name)

            if iso3:
                # Find the canonical DB row for this iso3.
                with connection.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM countries WHERE iso3 = %s LIMIT 1", [iso3]
                    )
                    row = cur.fetchone()

                if row is None:
                    errors.append(f"  WARN: no canonical row for iso3={iso3} (name='{name}')")
                    iso3 = None  # fall through to orphan path

                else:
                    canonical_id = row[0]
                    if canonical_id == country_id:
                        continue  # shouldn't happen but guard anyway

                    if not dry_run:
                        with connection.cursor() as cur:
                            # Reassign speakers
                            cur.execute(
                                "UPDATE speakers SET country_id=%s WHERE country_id=%s",
                                [canonical_id, country_id],
                            )
                            # Reassign resolution_sponsors
                            cur.execute(
                                "UPDATE resolution_sponsors SET country_id=%s WHERE country_id=%s",
                                [canonical_id, country_id],
                            )
                            # Reassign country_votes, skipping duplicates
                            cur.execute("""
                                UPDATE country_votes SET country_id = %s
                                WHERE country_id = %s
                                  AND NOT EXISTS (
                                    SELECT 1 FROM country_votes cv2
                                    WHERE cv2.vote_id = country_votes.vote_id
                                      AND cv2.country_id = %s
                                  )
                            """, [canonical_id, country_id, canonical_id])
                            # Delete any remaining votes (duplicates with canonical)
                            cur.execute(
                                "DELETE FROM country_votes WHERE country_id=%s",
                                [country_id],
                            )
                            # Delete the variant row
                            cur.execute(
                                "DELETE FROM countries WHERE id=%s", [country_id]
                            )

                    print(f"  {'[DRY] ' if dry_run else ''}REASSIGN {iso3}: '{name}'")
                    reassigned += 1
                    continue

            # No match — orphan speakers, delete votes/sponsors, delete row.
            if not dry_run:
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE speakers SET country_id=NULL WHERE country_id=%s",
                        [country_id],
                    )
                    cur.execute(
                        "DELETE FROM country_votes WHERE country_id=%s", [country_id]
                    )
                    cur.execute(
                        "DELETE FROM resolution_sponsors WHERE country_id=%s",
                        [country_id],
                    )
                    cur.execute(
                        "DELETE FROM countries WHERE id=%s", [country_id]
                    )

            orphaned += 1
            deleted  += 1

        if dry_run:
            transaction.set_rollback(True)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Done.")
    print(f"  Reassigned to canonical row : {reassigned}")
    print(f"  Orphaned (no match found)   : {orphaned}")
    print(f"  Rows deleted                : {reassigned + deleted}")
    if errors:
        print(f"\nWarnings ({len(errors)}):")
        for e in errors:
            print(e)


if __name__ == '__main__':
    main()
