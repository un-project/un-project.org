"""
Management command: populate_resolution_dates

For each resolution, derive an adoption date and write it to resolutions.date.

Priority:
  1. Any vote-document date that is plausible for the session (within ±1 year of
     the expected session year). The earliest such date is used.
  2. If no plausible document date exists:
       GA  → September 1 of expected_year  (placeholder year)
       SC  → January 1  of year parsed from the parenthetical in the symbol
             e.g. "2503(2019)" → 2019-01-01
  3. If nothing can be inferred, leave NULL.

Run with --overwrite to re-populate rows that already have a date.
"""

import re
from datetime import date

from django.core.management.base import BaseCommand
from django.db import connection


def _sc_year_from_symbol(symbol: str) -> int | None:
    """Extract year from SC symbol like '2503(2019)' or '757 (1992)'."""
    if not symbol:
        return None
    m = re.search(r'\((\d{4})\)', symbol)
    if m:
        y = int(m.group(1))
        if 1945 <= y <= 2030:
            return y
    return None


def _ga_expected_year(session: int) -> int:
    """GA session N opens in September of year (1945 + N). Session 2→1947, 64→2009, etc."""
    return 1945 + session


def _ga_session_from_symbol(symbol: str) -> int | None:
    """Parse GA session from resolution symbol (e.g. 'A/RES/31/127' or '31/127' → 31).

    More reliable than the DB session field, which can be wrong.
    """
    if not symbol:
        return None
    m = re.search(r'(?:A/RES/|A/)(\d+)/', symbol, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.match(r'^(\d+)/', symbol)
    if m:
        return int(m.group(1))
    return None


class Command(BaseCommand):
    help = 'Populate resolutions.date from vote document dates or session inference'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite', action='store_true',
            help='Re-populate resolutions that already have a date set',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']

        with connection.cursor() as cur:
            # Fetch all resolutions (with existing date if any)
            cur.execute("""
                SELECT id, body, session, adopted_symbol, draft_symbol, date
                FROM resolutions
                ORDER BY id
            """)
            resolutions = cur.fetchall()

            # Fetch all (resolution_id, document_date) pairs in one shot
            cur.execute("""
                SELECT DISTINCT v.resolution_id, d.date
                FROM votes v
                JOIN documents d ON d.id = v.document_id
                WHERE d.date IS NOT NULL
            """)
            doc_dates_raw = cur.fetchall()

        # Group document dates by resolution id
        from collections import defaultdict
        doc_dates = defaultdict(list)
        for res_id, dt in doc_dates_raw:
            if dt:
                doc_dates[res_id].append(dt)

        updates = []   # (date, resolution_id)
        skipped = unchanged = 0

        for res_id, body, session, adopted_sym, draft_sym, existing_date in resolutions:
            if existing_date and not overwrite:
                unchanged += 1
                continue

            symbol = adopted_sym or draft_sym or ''
            resolved = None

            # Prefer session derived from the symbol over the DB field, which
            # can be wrong (e.g. "31/127" has session=13 in old imports).
            sym_session = _ga_session_from_symbol(symbol) if body == 'GA' else None
            effective_session = sym_session if sym_session is not None else session

            if body == 'GA' and effective_session:
                expected_year = _ga_expected_year(effective_session)
                # Session N opens September of expected_year; resolutions are
                # adopted in expected_year or expected_year+1 (never before).
                plausible = [
                    d for d in doc_dates.get(res_id, [])
                    if 0 <= d.year - expected_year <= 1
                ]
                if plausible:
                    resolved = min(plausible)
                else:
                    resolved = date(expected_year, 9, 1)

            elif body == 'SC':
                sc_year = _sc_year_from_symbol(symbol)
                if sc_year:
                    plausible = [
                        d for d in doc_dates.get(res_id, [])
                        if abs(d.year - sc_year) <= 1
                    ]
                    if plausible:
                        resolved = min(plausible)
                    else:
                        resolved = date(sc_year, 1, 1)
                else:
                    # Fall back to any document date
                    all_dates = doc_dates.get(res_id, [])
                    if all_dates:
                        resolved = min(all_dates)

            else:
                # Unknown body or no session: use earliest document date
                all_dates = doc_dates.get(res_id, [])
                if all_dates:
                    resolved = min(all_dates)

            if resolved:
                updates.append((resolved, res_id))
            else:
                skipped += 1

        # Bulk update
        with connection.cursor() as cur:
            cur.executemany(
                "UPDATE resolutions SET date = %s WHERE id = %s",
                updates,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Updated {len(updates)} resolutions, '
            f'{unchanged} unchanged (already had date), '
            f'{skipped} skipped (no date inferable).'
        ))
