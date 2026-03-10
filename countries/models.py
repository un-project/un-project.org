from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=300, unique=True)
    short_name = models.CharField(max_length=100, null=True, blank=True)
    iso2 = models.CharField(max_length=2, null=True, blank=True, unique=True)
    iso3 = models.CharField(max_length=3, null=True, blank=True, unique=True)
    un_member_since = models.DateField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'countries'
        verbose_name_plural = 'countries'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        if self.iso3:
            return reverse('countries:detail', args=[self.iso3])
        return reverse('countries:detail_by_id', args=[self.pk])

    @property
    def flag_url(self):
        if self.iso3:
            return f'/static/flags/{self.iso3}.svg'
        return None

    @property
    def display_name(self):
        return self.short_name or self.name
