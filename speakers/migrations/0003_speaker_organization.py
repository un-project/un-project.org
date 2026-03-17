from django.db import migrations, models

ADD_ORGANIZATION_COLUMN = """
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'speakers') THEN
    ALTER TABLE speakers ADD COLUMN IF NOT EXISTS organization VARCHAR(400);
  END IF;
END $$;
"""

DROP_ORGANIZATION_COLUMN = """
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'speakers') THEN
    ALTER TABLE speakers DROP COLUMN IF EXISTS organization;
  END IF;
END $$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('speakers', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='speaker',
            name='organization',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.RunSQL(ADD_ORGANIZATION_COLUMN, reverse_sql=DROP_ORGANIZATION_COLUMN),
        migrations.AlterUniqueTogether(
            name='speaker',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='speaker',
            constraint=models.UniqueConstraint(fields=['name', 'country', 'organization'], name='uq_speaker'),
        ),
    ]
