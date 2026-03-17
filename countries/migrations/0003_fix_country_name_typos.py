"""
Fix typos in country names that were imported from UN documents.
"""
from django.db import migrations


def fix_typos(apps, schema_editor):
    db = schema_editor.connection

    def merge_into_correct(typo_name, correct_name):
        """
        Transfer iso codes from the typo row to the correct-name row,
        reassign all FK references (speakers, country_votes), then delete
        the typo row.  Falls back to a simple rename when no correct row
        exists yet.
        """
        with db.cursor() as cur:
            cur.execute("SELECT id, iso2, iso3, un_member_since FROM countries WHERE name = %s", [typo_name])
            typo_row = cur.fetchone()
            if typo_row is None:
                return
            typo_id, typo_iso2, typo_iso3, typo_since = typo_row

            cur.execute("SELECT id, iso2, iso3, un_member_since FROM countries WHERE name = %s", [correct_name])
            correct_row = cur.fetchone()

        if correct_row is None:
            # No canonical row – just rename in place.
            with db.cursor() as cur:
                cur.execute("UPDATE countries SET name = %s WHERE id = %s", [correct_name, typo_id])
            return

        correct_id, correct_iso2, correct_iso3, correct_since = correct_row

        # Clear unique codes on the typo row first to avoid constraint conflicts.
        with db.cursor() as cur:
            cur.execute("UPDATE countries SET iso2 = NULL, iso3 = NULL WHERE id = %s", [typo_id])

        # Set codes on the correct row (only fill blanks).
        new_iso3 = correct_iso3 or typo_iso3
        new_iso2 = correct_iso2 or typo_iso2
        new_since = correct_since or typo_since
        with db.cursor() as cur:
            cur.execute(
                "UPDATE countries SET iso2 = %s, iso3 = %s, un_member_since = %s WHERE id = %s",
                [new_iso2, new_iso3, new_since, correct_id],
            )

        # For speakers with the same name in both countries: reassign their speeches
        # to the canonical speaker, then delete the duplicate from the typo country.
        # For speakers only in the typo country: simply update country_id.
        with db.cursor() as cur:
            # Find typo speakers that already exist (by name) in the correct country.
            cur.execute(
                """
                SELECT s_typo.id AS typo_speaker_id, s_correct.id AS correct_speaker_id
                FROM speakers s_typo
                JOIN speakers s_correct
                  ON s_correct.name = s_typo.name
                 AND s_correct.country_id = %s
                WHERE s_typo.country_id = %s
                """,
                [correct_id, typo_id],
            )
            duplicates = cur.fetchall()

        for typo_speaker_id, correct_speaker_id in duplicates:
            with db.cursor() as cur:
                cur.execute(
                    "UPDATE speeches SET speaker_id = %s WHERE speaker_id = %s",
                    [correct_speaker_id, typo_speaker_id],
                )
                cur.execute("DELETE FROM speakers WHERE id = %s", [typo_speaker_id])

        with db.cursor() as cur:
            cur.execute("UPDATE speakers SET country_id = %s WHERE country_id = %s", [correct_id, typo_id])
            cur.execute("UPDATE country_votes SET country_id = %s WHERE country_id = %s", [correct_id, typo_id])
            cur.execute("DELETE FROM countries WHERE id = %s", [typo_id])

    # --- Pairs: typo has iso3, correct name has no iso3 ---
    merge_into_correct('United Arab Emiraes', 'United Arab Emirates')
    merge_into_correct('Demark', 'Denmark')
    merge_into_correct('Irag', 'Iraq')
    merge_into_correct("Cote d'lvoire", "Côte d'Ivoire")
    merge_into_correct('Lichtenstein', 'Liechtenstein')
    merge_into_correct('Marshal Islands', 'Marshall Islands')
    merge_into_correct('Mozambigue', 'Mozambique')

    # --- Typos whose correct name already has the iso3 ---
    merge_into_correct('Kyrzgystan', 'Kyrgyzstan')
    merge_into_correct('Liechenstein', 'Liechtenstein')
    merge_into_correct('Liechstenstein', 'Liechtenstein')
    merge_into_correct('Sweden\xad', 'Sweden')       # soft-hyphen suffix
    merge_into_correct('Syrian Arabic Republic', 'Syrian Arab Republic')

    # --- Libya name-variant typos ---
    # Rename 'Libya Arab Jamahiriya' (missing 'n') to the proper spelling, then
    # merge the second typo variant into that row.
    merge_into_correct('Libya Arab Jamahiriya', 'Libyan Arab Jamahiriya')
    merge_into_correct('Libyan Arab Jamahariya', 'Libyan Arab Jamahiriya')


class Migration(migrations.Migration):

    dependencies = [
        ('countries', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(fix_typos, migrations.RunPython.noop),
    ]
