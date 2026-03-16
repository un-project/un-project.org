from django.db import models


class Resolution(models.Model):
    draft_symbol = models.CharField(max_length=50)
    adopted_symbol = models.CharField(max_length=50, null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    body = models.CharField(max_length=2)
    session = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'resolutions'
        ordering = ['draft_symbol']

    def __str__(self):
        return self.adopted_symbol or self.draft_symbol

    @property
    def slug(self):
        symbol = self.adopted_symbol or self.draft_symbol
        return symbol.replace('/', '-').replace('.', '-')

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('votes:resolution_detail', args=[self.slug])

    # URL prefixes as constants to prevent the linter from lowercasing them.
    _DOCS_PREFIX = {
        'GA': 'https://docs.un.org/en/a/res/',
        'SC': 'https://docs.un.org/en/S/RES/',
    }

    @property
    def docs_un_url(self):
        prefix = self._DOCS_PREFIX.get(self.body)
        if not self.adopted_symbol or prefix is None:
            return None
        return prefix + self.adopted_symbol


class Vote(models.Model):
    VOTE_TYPE_CHOICES = [
        ('consensus', 'Consensus'),
        ('recorded', 'Recorded Vote'),
    ]
    VOTE_SCOPE_CHOICES = [
        ('whole_resolution', 'Whole Resolution'),
        ('paragraph', 'Paragraph'),
        ('amendment', 'Amendment'),
    ]

    document = models.ForeignKey(
        'meetings.Document', on_delete=models.CASCADE, related_name='votes'
    )
    item = models.ForeignKey(
        'meetings.DocumentItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='votes'
    )
    resolution = models.ForeignKey(Resolution, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=20, choices=VOTE_TYPE_CHOICES)
    vote_scope = models.CharField(max_length=20, choices=VOTE_SCOPE_CHOICES)
    paragraph_number = models.IntegerField(null=True, blank=True)
    yes_count = models.IntegerField(null=True, blank=True)
    no_count = models.IntegerField(null=True, blank=True)
    abstain_count = models.IntegerField(null=True, blank=True)
    position_in_item = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'votes'

    def __str__(self):
        return f'Vote on {self.resolution} at {self.document}'


class CountryVote(models.Model):
    VOTE_POSITION_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('abstain', 'Abstain'),
        ('absent', 'Absent'),
    ]

    vote = models.ForeignKey(Vote, on_delete=models.CASCADE, related_name='country_votes')
    country = models.ForeignKey(
        'countries.Country', on_delete=models.CASCADE, related_name='country_votes'
    )
    vote_position = models.CharField(max_length=10, choices=VOTE_POSITION_CHOICES)

    class Meta:
        managed = False
        db_table = 'country_votes'
        constraints = [
            models.UniqueConstraint(fields=['vote', 'country'], name='uq_country_vote')
        ]

    def __str__(self):
        return f'{self.country} voted {self.vote_position} on {self.vote}'
