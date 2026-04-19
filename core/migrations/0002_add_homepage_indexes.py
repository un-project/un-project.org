from django.db import migrations


class Migration(migrations.Migration):
    """Add indexes for the three most expensive homepage queries.

    - documents(date DESC, meeting_number DESC) — recent meetings ORDER BY
    - documents(body, date)                     — body-filtered meetings
    - speeches(document_id)                     — speech → document JOIN
    - votes(document_id)                        — vote → document JOIN / ORDER BY
    """

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_documents_date
                ON public.documents (date DESC, meeting_number DESC);

            CREATE INDEX IF NOT EXISTS idx_documents_body_date
                ON public.documents (body, date DESC);

            CREATE INDEX IF NOT EXISTS idx_speeches_document_id
                ON public.speeches (document_id);

            CREATE INDEX IF NOT EXISTS idx_votes_document_id
                ON public.votes (document_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS public.idx_documents_date;
            DROP INDEX IF EXISTS public.idx_documents_body_date;
            DROP INDEX IF EXISTS public.idx_speeches_document_id;
            DROP INDEX IF EXISTS public.idx_votes_document_id;
            """,
        ),
    ]
