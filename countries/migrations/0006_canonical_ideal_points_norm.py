from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('countries', '0005_canonical_ideal_points'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE VIEW canonical_ideal_points_norm AS
                WITH us_signs AS (
                    SELECT year,
                           CASE WHEN ideal_point >= 0 THEN 1.0 ELSE -1.0 END AS sgn
                    FROM canonical_ideal_points
                    WHERE iso3 = 'USA'
                )
                SELECT cip.id,
                       cip.country_id,
                       cip.iso3,
                       cip.year,
                       cip.ideal_point * COALESCE(s.sgn, 1.0) AS ideal_point,
                       cip.se,
                       cip.source
                FROM canonical_ideal_points cip
                LEFT JOIN us_signs s ON s.year = cip.year;
            """,
            reverse_sql="DROP VIEW IF EXISTS canonical_ideal_points_norm;",
        ),
    ]
