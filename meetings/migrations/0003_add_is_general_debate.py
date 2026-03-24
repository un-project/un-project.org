from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE documents ADD COLUMN IF NOT EXISTS is_general_debate BOOLEAN NOT NULL DEFAULT FALSE;",
            reverse_sql="ALTER TABLE documents DROP COLUMN IF EXISTS is_general_debate;",
        ),
    ]
