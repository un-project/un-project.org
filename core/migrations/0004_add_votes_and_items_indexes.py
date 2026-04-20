from django.db import migrations


class Migration(migrations.Migration):
    """Add indexes for /votes/ and /meeting/agenda/ queries.

    votes(vote_type)       — filter by recorded/procedural
    votes(resolution_id)   — JOIN to resolutions
    votes(no_count)        — ORDER BY for most-contested
    document_items(item_type)   — filter agenda items
    document_items(document_id) — JOIN to documents
    """

    dependencies = [
        ('core', '0003_add_country_votes_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_votes_vote_type
                ON public.votes (vote_type);

            CREATE INDEX IF NOT EXISTS idx_votes_resolution_id
                ON public.votes (resolution_id);

            CREATE INDEX IF NOT EXISTS idx_votes_no_count
                ON public.votes (no_count DESC NULLS LAST);

            CREATE INDEX IF NOT EXISTS idx_document_items_item_type
                ON public.document_items (item_type);

            CREATE INDEX IF NOT EXISTS idx_document_items_document_id
                ON public.document_items (document_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS public.idx_votes_vote_type;
            DROP INDEX IF EXISTS public.idx_votes_resolution_id;
            DROP INDEX IF EXISTS public.idx_votes_no_count;
            DROP INDEX IF EXISTS public.idx_document_items_item_type;
            DROP INDEX IF EXISTS public.idx_document_items_document_id;
            """,
        ),
    ]
