from django.db import migrations


class Migration(migrations.Migration):
    """Index speeches(speaker_id) for fast speech-count annotation on speaker list."""

    dependencies = [
        ('core', '0004_add_votes_and_items_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_speeches_speaker_id ON public.speeches (speaker_id);",
            reverse_sql="DROP INDEX IF EXISTS public.idx_speeches_speaker_id;",
        ),
    ]
