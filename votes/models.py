from django.db import models


# Voeten issue-code definitions: (field_suffix, short_label, long_label)
ISSUE_CODES = [
    ('me', 'Middle East',     'Middle East'),
    ('nu', 'Nuclear/Arms',    'Nuclear weapons & arms control'),
    ('co', 'Colonialism',     'Colonialism'),
    ('hr', 'Human Rights',    'Human rights'),
    ('ec', 'Economic Dev.',   'Economic development'),
    ('di', 'Disarmament',     'Disarmament / Cold War'),
]


class Resolution(models.Model):
    draft_symbol = models.CharField(max_length=50)
    adopted_symbol = models.CharField(max_length=50, null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    body = models.CharField(max_length=2)
    session = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    full_text = models.TextField(null=True, blank=True)
    draft_text = models.TextField(null=True, blank=True)
    crunsc_id = models.CharField(max_length=30, null=True, blank=True)
    important_vote = models.BooleanField(null=True, blank=True)
    issue_me = models.BooleanField(null=True, blank=True)  # Middle East
    issue_nu = models.BooleanField(null=True, blank=True)  # Nuclear / arms control
    issue_co = models.BooleanField(null=True, blank=True)  # Colonialism
    issue_hr = models.BooleanField(null=True, blank=True)  # Human rights
    issue_ec = models.BooleanField(null=True, blank=True)  # Economic development
    issue_di = models.BooleanField(null=True, blank=True)  # Disarmament / Cold War

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

    @property
    def issue_labels(self):
        """Return list of (code, short_label) for all active Voeten issue flags."""
        return [
            (code, short)
            for code, short, _long in ISSUE_CODES
            if getattr(self, f'issue_{code}')
        ]

    @property
    def docs_un_url(self):
        if not self.adopted_symbol:
            return None
        symbol = self.adopted_symbol
        # Some symbols are stored as full UN symbols (e.g. "A/RES/77/301" or
        # "S/RES/2503(2019)"); others as bare numeric forms ("77/301" or
        # "2503(2019)").  Normalise to a full symbol so no prefix is doubled.
        upper = symbol.upper()
        if self.body == 'GA' and not upper.startswith('A/RES/'):
            symbol = f'A/RES/{symbol}'
        elif self.body == 'SC' and not upper.startswith('S/RES/'):
            symbol = f'S/RES/{symbol}'
        elif self.body not in ('GA', 'SC'):
            return None
        return f'https://docs.un.org/en/{symbol}'


class ResolutionSponsor(models.Model):
    resolution = models.ForeignKey(
        Resolution, on_delete=models.CASCADE, related_name='sponsors'
    )
    country = models.ForeignKey(
        'countries.Country', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sponsored_resolutions'
    )
    country_name = models.TextField()

    class Meta:
        managed = False
        db_table = 'resolution_sponsors'

    def __str__(self):
        return f'{self.country_name} → {self.resolution}'


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


class Veto(models.Model):
    dppa_id = models.IntegerField(unique=True)
    draft_symbol = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    meeting_symbol = models.CharField(max_length=30, null=True, blank=True)
    document = models.ForeignKey(
        'meetings.Document', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vetoes'
    )
    agenda = models.TextField(null=True, blank=True)
    short_agenda = models.TextField(null=True, blank=True)
    n_vetoing_pm = models.IntegerField(null=True, blank=True)
    dppa_url = models.CharField(max_length=500, null=True, blank=True)
    vetoing_countries = models.ManyToManyField(
        'countries.Country', through='VetoCountry', related_name='vetoes'
    )

    class Meta:
        managed = False
        db_table = 'vetoes'
        ordering = ['-date']

    def __str__(self):
        return self.draft_symbol or f'Veto #{self.dppa_id}'

    @property
    def doc_url(self):
        if self.draft_symbol:
            return f'https://docs.un.org/en/{self.draft_symbol}'
        return self.dppa_url or None


class VetoCountry(models.Model):
    veto = models.ForeignKey(Veto, on_delete=models.CASCADE, related_name='veto_countries')
    country = models.ForeignKey(
        'countries.Country', on_delete=models.CASCADE, related_name='veto_countries'
    )

    class Meta:
        managed = False
        db_table = 'veto_countries'
        unique_together = [('veto', 'country')]


class VotingBloc(models.Model):
    country = models.ForeignKey(
        'countries.Country', on_delete=models.CASCADE, related_name='detected_blocs'
    )
    year = models.IntegerField()
    bloc_index = models.IntegerField()
    window_start = models.IntegerField()
    window_end = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'voting_blocs'
        unique_together = [('country', 'year')]

    def __str__(self):
        return f'Bloc {self.bloc_index} ({self.year}): {self.country}'


class ResolutionCitation(models.Model):
    citing = models.ForeignKey(
        Resolution, on_delete=models.CASCADE, related_name='outgoing_citations',
        db_column='citing_id',
    )
    cited_symbol = models.CharField(max_length=100)
    cited = models.ForeignKey(
        Resolution, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='incoming_citations', db_column='cited_id',
    )
    weight = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'resolution_citations'
        unique_together = [('citing', 'cited_symbol')]

    def __str__(self):
        return f'{self.citing} → {self.cited_symbol}'
