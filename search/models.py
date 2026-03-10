from django.db import models


class SpeechSearchIndex(models.Model):
    """
    Materialized view for full-text search on speeches.
    Created by migration 0001_create_search_index.
    """
    speech_id = models.IntegerField(primary_key=True)
    document_id = models.IntegerField()
    symbol = models.CharField(max_length=30)
    date = models.DateField(null=True)
    body = models.CharField(max_length=2)
    session = models.IntegerField()
    speaker_id = models.IntegerField()
    speaker_name = models.CharField(max_length=300)
    country_id = models.IntegerField(null=True)
    country_name = models.CharField(max_length=300, null=True)
    text = models.TextField()
    search_vector = models.TextField()  # tsvector stored as text placeholder

    class Meta:
        managed = False
        db_table = 'speech_search_index'
