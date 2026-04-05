from django.db import models


class SCRepresentative(models.Model):
    country = models.ForeignKey(
        'countries.Country',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sc_representatives',
    )
    speaker = models.ForeignKey(
        'speakers.Speaker',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sc_representative_records',
    )
    name = models.TextField()
    salutation = models.CharField(max_length=20, null=True, blank=True)
    sc_president = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    undl_id = models.CharField(max_length=50, null=True, blank=True)
    undl_link = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'sc_representatives'

    def __str__(self):
        return self.name


class Speaker(models.Model):
    name = models.CharField(max_length=300)
    country = models.ForeignKey(
        'countries.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='speakers',
    )
    role = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=20, null=True, blank=True)
    organization = models.CharField(max_length=400, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'speakers'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'country', 'organization'], name='uq_speaker')
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('speakers:detail', args=[self.pk])
