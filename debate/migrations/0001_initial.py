from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('countries', '0001_initial'),
        ('meetings', '0001_initial'),
        ('speakers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneralDebateEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('speaker_name', models.TextField()),
                ('salutation', models.CharField(blank=True, max_length=20, null=True)),
                ('ga_session', models.IntegerField()),
                ('meeting_date', models.DateField(blank=True, null=True)),
                ('undl_id', models.CharField(blank=True, max_length=30, null=True)),
                ('undl_link', models.TextField(blank=True, null=True)),
                ('document', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='debate_entries',
                    to='meetings.document',
                )),
                ('country', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='debate_entries',
                    to='countries.country',
                )),
                ('speaker', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='debate_entries',
                    to='speakers.speaker',
                )),
            ],
            options={
                'db_table': 'general_debate_entries',
                'managed': False,
                'ordering': ['ga_session', 'meeting_date', 'id'],
            },
        ),
    ]
