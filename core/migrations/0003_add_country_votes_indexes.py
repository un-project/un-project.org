from django.db import migrations


class Migration(migrations.Migration):
    """Add indexes for the voting similarity self-join on country_votes.

    The similarity query does:
      FROM country_votes cv1                      -- needs (country_id)
      JOIN country_votes cv2 ON cv1.vote_id = cv2.vote_id  -- needs (vote_id)

    Without these, both scans are sequential across the full table.
    """

    dependencies = [
        ('core', '0002_add_homepage_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_country_votes_country_id
                ON public.country_votes (country_id);

            CREATE INDEX IF NOT EXISTS idx_country_votes_vote_id
                ON public.country_votes (vote_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS public.idx_country_votes_country_id;
            DROP INDEX IF EXISTS public.idx_country_votes_vote_id;
            """,
        ),
    ]
