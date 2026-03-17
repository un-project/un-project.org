"""
Fix country rows where iso3 codes were assigned to garbled/partial names
instead of the canonical name that holds the actual vote/speaker data.

For each affected iso3 code:
  1. Clear iso codes from the wrong row to avoid uniqueness conflicts.
  2. Set the codes on the canonical row.
  3. Reassign all FK references (speakers, country_votes) from the wrong row
     to the canonical row (handling duplicate speakers via speeches reassignment).
  4. Delete the wrong row.
"""
from django.db import migrations


def _merge(db, wrong_name, canonical_name):
    """
    Transfer iso codes and all FK data from *wrong_name* into *canonical_name*,
    then delete the *wrong_name* row.
    If *canonical_name* does not exist, rename *wrong_name* in place.
    """
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, iso2, iso3, un_member_since FROM countries WHERE name = %s",
            [wrong_name],
        )
        wrong_row = cur.fetchone()
        if wrong_row is None:
            return
        wrong_id, wrong_iso2, wrong_iso3, wrong_since = wrong_row

        cur.execute(
            "SELECT id, iso2, iso3, un_member_since FROM countries WHERE name = %s",
            [canonical_name],
        )
        canonical_row = cur.fetchone()

    if canonical_row is None:
        # No canonical row exists – just rename in place.
        with db.cursor() as cur:
            cur.execute("UPDATE countries SET name = %s WHERE id = %s", [canonical_name, wrong_id])
        return

    canonical_id, canon_iso2, canon_iso3, canon_since = canonical_row

    # Clear unique codes on the wrong row first to avoid constraint violations.
    with db.cursor() as cur:
        cur.execute("UPDATE countries SET iso2 = NULL, iso3 = NULL WHERE id = %s", [wrong_id])

    # Copy codes to canonical (only fill blanks).
    with db.cursor() as cur:
        cur.execute(
            "UPDATE countries SET iso2 = %s, iso3 = %s, un_member_since = %s WHERE id = %s",
            [
                canon_iso2 or wrong_iso2,
                canon_iso3 or wrong_iso3,
                canon_since or wrong_since,
                canonical_id,
            ],
        )

    # Speakers: reassign speeches from duplicates, then delete duplicate, then bulk-update.
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT s_wrong.id AS wrong_speaker_id, s_canon.id AS canon_speaker_id
            FROM speakers s_wrong
            JOIN speakers s_canon
              ON s_canon.name = s_wrong.name
             AND s_canon.country_id = %s
            WHERE s_wrong.country_id = %s
            """,
            [canonical_id, wrong_id],
        )
        duplicates = cur.fetchall()

    for wrong_speaker_id, canon_speaker_id in duplicates:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE speeches SET speaker_id = %s WHERE speaker_id = %s",
                [canon_speaker_id, wrong_speaker_id],
            )
            cur.execute("DELETE FROM speakers WHERE id = %s", [wrong_speaker_id])

    with db.cursor() as cur:
        cur.execute(
            "UPDATE speakers SET country_id = %s WHERE country_id = %s",
            [canonical_id, wrong_id],
        )
        # country_votes: delete rows that already exist for the canonical country
        # (same vote_id), then reassign the rest.
        cur.execute(
            """
            DELETE FROM country_votes
            WHERE country_id = %s
              AND vote_id IN (
                  SELECT vote_id FROM country_votes WHERE country_id = %s
              )
            """,
            [wrong_id, canonical_id],
        )
        cur.execute(
            "UPDATE country_votes SET country_id = %s WHERE country_id = %s",
            [canonical_id, wrong_id],
        )
        cur.execute("DELETE FROM countries WHERE id = %s", [wrong_id])


def fix_misassigned_codes(apps, schema_editor):
    db = schema_editor.connection

    # --- iso3 assigned to garbled/partial names ---
    # The canonical names hold the actual vote and speaker data.
    _merge(db, 'Kingdom of the Netherlands', 'Netherlands')
    _merge(db, 'Cape', 'Luxembourg')
    _merge(db, 'Aviva', 'San Marino')
    _merge(db, 'Solomon', 'Solomon Islands')
    _merge(db, 'Saint Vincent and', 'Saint Vincent and the Grenadines')
    _merge(db, 'Timor- Leste', 'Timor-Leste')
    _merge(db, 'Guinea Bissau', 'Guinea-Bissau')
    _merge(db, 'Saint', 'Saint Kitts and Nevis')

    # --- Netherlands variant with one vote ---
    _merge(db, 'Netherlands (Kingdom of the)', 'Netherlands')

    # --- Guinea-Bissau space-hyphen variant ---
    _merge(db, 'Guinea- Bissau', 'Guinea-Bissau')

    # --- Kazakstan old transliteration ---
    _merge(db, 'Kazakstan', 'Kazakhstan')

    # --- Côte d'Ivoire apostrophe/accent variants ---
    # Canonical: "Côte d'Ivoire" (straight apostrophe, has CIV iso3, id kept)
    # Merge curly-apostrophe+accents variant (has 241 votes) into canonical.
    _merge(db, 'C\xf4te d\u2019Ivoire', "C\xf4te d'Ivoire")
    # Merge no-accents curly-apostrophe variant (0 votes).
    _merge(db, 'Cote d\u2019Ivoire', "C\xf4te d'Ivoire")
    # Remove backslash-prefix garbage variant.
    _merge(db, "\\ Cote d'lvoire", "C\xf4te d'Ivoire")


class Migration(migrations.Migration):

    dependencies = [
        ('countries', '0003_fix_country_name_typos'),
    ]

    operations = [
        migrations.RunPython(fix_misassigned_codes, migrations.RunPython.noop),
    ]
