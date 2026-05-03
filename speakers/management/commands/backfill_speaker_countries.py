"""
Management command: backfill_speaker_countries

Speakers imported from PDFs sometimes have their country stored in the
`organization` field instead of `country_id`, because the affiliation
string (e.g. "Union of Soviet Socialist Republics") contains a keyword
that the extractor's `is_organization()` check treats as an org keyword
("union", "community", etc.).

This command:
1. Exact match: sets country_id for speakers whose `organization` matches
   a country name exactly (case-insensitive).
2. Pattern match: handles common OCR garbles of known countries (e.g.
   "Union of Soviet…" variants → USSR).

After setting country_id the organization field is cleared so the country
shows as a flag rather than text.
"""

import re
from django.core.management.base import BaseCommand
from django.db import connection


# OCR variants that are clearly a specific country.
# Each entry: (regex pattern, country iso3)
_PATTERN_FIXES = [
    # All "Union of Soviet…" variants → USSR
    (re.compile(r"union\s+of\s+s[ao]v[iy]et\b", re.IGNORECASE), "SUN"),
    # Byelorussian variants (should be Belarus — already a separate member)
    (re.compile(r"byelo?russian\s+soviet", re.IGNORECASE), "BLR"),
    # Ukrainian SSR variants
    (re.compile(r"ukrainian\s+soviet", re.IGNORECASE), "UKR"),
]


class Command(BaseCommand):
    help = "Backfill speaker country_id from organization field"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Report what would be changed without writing",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        total_fixed = 0

        # --- Pass 1: exact case-insensitive match on country name ---
        if not dry_run:
            with connection.cursor() as cur:
                cur.execute("""
                    UPDATE speakers s
                    SET country_id = c.id,
                        organization = NULL
                    FROM countries c
                    WHERE s.country_id IS NULL
                      AND s.organization IS NOT NULL
                      AND LOWER(TRIM(s.organization)) = LOWER(c.name)
                    RETURNING s.id
                """)
                exact_fixed = cur.rowcount
        else:
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM speakers s
                    JOIN countries c
                      ON LOWER(TRIM(s.organization)) = LOWER(c.name)
                    WHERE s.country_id IS NULL AND s.organization IS NOT NULL
                """)
                exact_fixed = cur.fetchone()[0]

        self.stdout.write(f"  Exact name match: {exact_fixed} speakers")
        total_fixed += exact_fixed

        # --- Pass 2: pattern-based fixes for OCR garbles ---
        with connection.cursor() as cur:
            cur.execute("""
                SELECT s.id, s.organization, c.id as country_id
                FROM speakers s
                CROSS JOIN countries c
                WHERE s.country_id IS NULL
                  AND s.organization IS NOT NULL
                  AND c.iso3 IN %s
            """, [tuple(iso3 for _, iso3 in _PATTERN_FIXES)])
            candidates = cur.fetchall()

        # Build iso3 → country_id map
        iso3_to_id = {}
        with connection.cursor() as cur:
            cur.execute("SELECT iso3, id FROM countries WHERE iso3 IN %s",
                        [tuple(iso3 for _, iso3 in _PATTERN_FIXES)])
            for iso3, cid in cur.fetchall():
                iso3_to_id[iso3] = cid

        pattern_updates = []
        for speaker_id, org, _ in candidates:
            for pattern, iso3 in _PATTERN_FIXES:
                if pattern.search(org or ""):
                    cid = iso3_to_id.get(iso3)
                    if cid:
                        pattern_updates.append((cid, speaker_id))
                    break

        if pattern_updates and not dry_run:
            with connection.cursor() as cur:
                cur.executemany(
                    "UPDATE speakers SET country_id = %s, organization = NULL WHERE id = %s",
                    pattern_updates,
                )

        self.stdout.write(f"  Pattern match (OCR variants): {len(pattern_updates)} speakers")
        total_fixed += len(pattern_updates)

        verb = "Would fix" if dry_run else "Fixed"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} {total_fixed} speakers total."
        ))
