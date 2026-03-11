from django.db import models
from django.contrib.postgres.search import SearchVectorField


class SpeechSearchIndex(models.Model):
    """Legacy materialized view — superseded by SearchIndex."""
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
    search_vector = models.TextField()

    class Meta:
        managed = False
        db_table = 'speech_search_index'


class SearchIndex(models.Model):
    """
    Unified full-text search index (materialized view: search_index).
    Covers speeches and resolutions with weighted tsvectors.
    Refresh with: manage.py refresh_search_index
    """
    id = models.BigIntegerField(primary_key=True)
    item_type = models.CharField(max_length=20)       # 'speech' | 'resolution'
    item_id = models.IntegerField()
    document_id = models.IntegerField(null=True)
    document_symbol = models.CharField(max_length=50, null=True)
    date = models.DateField(null=True)
    body = models.CharField(max_length=2, null=True)
    session = models.IntegerField(null=True)
    speaker_id = models.IntegerField(null=True)
    speaker_name = models.CharField(max_length=300, null=True)
    country_id = models.IntegerField(null=True)
    country_name = models.CharField(max_length=300, null=True)
    country_iso3 = models.CharField(max_length=3, null=True)
    content = models.TextField()
    search_vector = SearchVectorField()

    class Meta:
        managed = False
        db_table = 'search_index'

    @property
    def document_slug(self):
        if self.document_symbol:
            return self.document_symbol.replace('/', '-').replace('.', '-')
        return None
