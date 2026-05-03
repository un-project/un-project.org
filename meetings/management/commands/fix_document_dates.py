"""
Management command: fix_document_dates

Nulls out document dates that are implausible given the session number
encoded in the document symbol (e.g. A/71/PV.2 → session 71 → expected
year ~2016; a stored date of 1991 is clearly an OCR error).

For GA documents: acceptable range is [expected_year, expected_year + 2]
  (session N opens September of 1945+N; meetings span ~12 months).
For SC documents: no session in symbol, so only extreme outliers are
  caught via a minimum date check (SC founded 1946).

After running this command, re-run import_undl_votes (extractor) to
backfill correct dates from the authoritative DHL vote CSV.
"""

import re
from django.core.management.base import BaseCommand
from django.db import connection


def _ga_session_from_symbol(symbol: str) -> int | None:
    m = re.search(r"A/(\d+)/PV\.", symbol, re.IGNORECASE)
    return int(m.group(1)) if m else None


class Command(BaseCommand):
    help = "Null out document dates that are implausible for their session"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Report what would be changed without modifying the DB",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        with connection.cursor() as cur:
            cur.execute("""
                SELECT id, symbol, session, date, body
                FROM documents
                WHERE date IS NOT NULL
                  AND (
                      (body = 'GA' AND session IS NOT NULL AND session > 0)
                      OR body = 'SC'
                  )
                ORDER BY symbol
            """)
            docs = cur.fetchall()

        nulled = 0
        to_null = []

        for doc_id, symbol, session, doc_date, body in docs:
            implausible = False

            if body == "GA" and session:
                expected_year = 1945 + session
                if not (0 <= doc_date.year - expected_year <= 2):
                    implausible = True

            elif body == "SC":
                # SC meetings started in 1946; any date before that is wrong
                if doc_date.year < 1946:
                    implausible = True

            if implausible:
                if dry_run:
                    exp = f"~{1945 + session}" if body == "GA" and session else "≥1946"
                    self.stdout.write(
                        f"  {symbol}  date={doc_date}  expected={exp}"
                    )
                else:
                    to_null.append(doc_id)
                nulled += 1

        if not dry_run and to_null:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE documents SET date = NULL WHERE id = ANY(%s)",
                    [to_null],
                )

        verb = "Would null" if dry_run else "Nulled"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} {nulled} implausible document dates.")
        )
