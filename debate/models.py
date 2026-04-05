from django.db import models


class GeneralDebateEntry(models.Model):
    document = models.ForeignKey(
        'meetings.Document', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='debate_entries',
    )
    country = models.ForeignKey(
        'countries.Country', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='debate_entries',
    )
    speaker = models.ForeignKey(
        'speakers.Speaker', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='debate_entries',
    )
    speaker_name = models.TextField()
    salutation = models.CharField(max_length=20, null=True, blank=True)
    ga_session = models.IntegerField()
    meeting_date = models.DateField(null=True, blank=True)
    undl_id = models.CharField(max_length=30, null=True, blank=True)
    undl_link = models.TextField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'general_debate_entries'
        ordering = ['ga_session', 'meeting_date', 'id']

    def __str__(self):
        return f'Session {self.ga_session} — {self.speaker_name}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('debate:entry', args=[self.ga_session, self.pk])
