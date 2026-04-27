from django.contrib.postgres.fields import ArrayField
from django.db import models


class Speech(models.Model):
    document = models.ForeignKey(
        'meetings.Document', on_delete=models.CASCADE, related_name='speeches'
    )
    item = models.ForeignKey(
        'meetings.DocumentItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='speeches'
    )
    speaker = models.ForeignKey(
        'speakers.Speaker', on_delete=models.CASCADE, related_name='speeches'
    )
    language = models.CharField(max_length=50, null=True, blank=True)
    on_behalf_of = models.CharField(max_length=300, null=True, blank=True)
    text = models.TextField()
    position_in_document = models.IntegerField()
    position_in_item = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'speeches'
        ordering = ['position_in_document']

    def __str__(self):
        return f'Speech by {self.speaker} at {self.document}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('meetings:detail', args=[self.document.slug]) + f'#speech-{self.pk}'

    @property
    def excerpt(self):
        return self.text[:300] + ('…' if len(self.text) > 300 else '')


class StageDirection(models.Model):
    DIRECTION_TYPES = [
        ('adoption', 'Adoption'),
        ('decision', 'Decision'),
        ('suspension', 'Suspension'),
        ('resumption', 'Resumption'),
        ('adjournment', 'Adjournment'),
        ('silence', 'Silence'),
        ('language_note', 'Language Note'),
        ('other', 'Other'),
    ]

    document = models.ForeignKey(
        'meetings.Document', on_delete=models.CASCADE, related_name='stage_directions'
    )
    item = models.ForeignKey(
        'meetings.DocumentItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='stage_directions'
    )
    text = models.TextField()
    direction_type = models.CharField(max_length=20, choices=DIRECTION_TYPES)
    position_in_document = models.IntegerField()
    position_in_item = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'stage_directions'
        ordering = ['position_in_document']

    def __str__(self):
        return f'[{self.direction_type}] {self.text[:60]}'


class Topic(models.Model):
    topic_num = models.IntegerField()
    label = models.TextField()
    keywords = ArrayField(models.TextField())
    model = models.CharField(max_length=50)
    n_topics = models.IntegerField()
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'topics'

    def __str__(self):
        return self.label


class SpeechTopic(models.Model):
    speech = models.ForeignKey(Speech, on_delete=models.CASCADE, related_name='speech_topics')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='speech_topics')
    weight = models.FloatField()

    class Meta:
        managed = False
        db_table = 'speech_topics'
