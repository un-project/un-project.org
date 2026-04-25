from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('countries', '0004_fix_misassigned_iso_codes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE VIEW canonical_ideal_points AS
                SELECT DISTINCT ON (country_id, year)
                    id, country_id, iso3, year, ideal_point, se, source
                FROM country_ideal_points
                WHERE ideal_point IS NOT NULL
                ORDER BY
                    country_id,
                    year,
                    CASE source
                        WHEN 'bsv2017_mcmc'   THEN 1
                        WHEN 'voeten_bsv2017' THEN 2
                        WHEN 'computed_irt'   THEN 3
                        ELSE 4
                    END;
            """,
            reverse_sql="DROP VIEW IF EXISTS canonical_ideal_points;",
        ),
    ]
