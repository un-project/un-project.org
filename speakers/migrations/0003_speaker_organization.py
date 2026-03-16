from django.db import migrations, models


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
        migrations.AlterUniqueTogether(
            name='speaker',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='speaker',
            constraint=models.UniqueConstraint(fields=['name', 'country', 'organization'], name='uq_speaker'),
        ),
    ]
