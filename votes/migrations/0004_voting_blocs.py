from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('votes', '0003_vetoes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS voting_blocs (
                    id          SERIAL PRIMARY KEY,
                    country_id  INTEGER NOT NULL,
                    year        INTEGER NOT NULL,
                    bloc_index  INTEGER NOT NULL,
                    window_start INTEGER NOT NULL,
                    window_end   INTEGER NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS voting_blocs_country_year
                    ON voting_blocs(country_id, year);
                CREATE INDEX IF NOT EXISTS voting_blocs_year
                    ON voting_blocs(year);
            """,
            reverse_sql="DROP TABLE IF EXISTS voting_blocs;",
        ),
    ]
