from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('votes', '0004_voting_blocs'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE resolutions ADD COLUMN IF NOT EXISTS date DATE;",
            reverse_sql="ALTER TABLE resolutions DROP COLUMN IF EXISTS date;",
        ),
    ]
