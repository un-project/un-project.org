from django.db import models


class Document(models.Model):
    BODY_GA = 'GA'
    BODY_SC = 'SC'
    BODY_CHOICES = [
        (BODY_GA, 'General Assembly'),
        (BODY_SC, 'Security Council'),
    ]

    symbol = models.CharField(max_length=30, unique=True)
    body = models.CharField(max_length=2, choices=BODY_CHOICES)
    meeting_number = models.IntegerField()
    session = models.IntegerField()
    date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    pdf_path = models.CharField(max_length=500, null=True, blank=True)
    is_general_debate = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'documents'
        ordering = ['-date', '-meeting_number']

    def __str__(self):
        return self.symbol

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('meetings:detail', args=[self.slug])

    @property
    def slug(self):
        import re
        s = self.symbol.replace('/', '-').replace('.', '-')
        s = re.sub(r'[^-a-zA-Z0-9_]', '-', s)
        s = re.sub(r'-{2,}', '-', s).strip('-')
        return s

    @property
    def body_display(self):
        return dict(self.BODY_CHOICES).get(self.body, self.body)

    @property
    def docs_un_url(self):
        return f'https://docs.un.org/en/{self.symbol}'


class DocumentItem(models.Model):
    ITEM_TYPE_AGENDA = 'agenda_item'
    ITEM_TYPE_OTHER = 'other_item'
    ITEM_TYPE_CHOICES = [
        (ITEM_TYPE_AGENDA, 'Agenda Item'),
        (ITEM_TYPE_OTHER, 'Other Item'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='items')
    position = models.IntegerField()
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    title = models.TextField()
    agenda_number = models.IntegerField(null=True, blank=True)
    sub_item = models.CharField(max_length=10, null=True, blank=True)
    continued = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'document_items'
        ordering = ['position']
        constraints = [
            models.UniqueConstraint(fields=['document', 'position'], name='uq_item_position')
        ]

    def __str__(self):
        return f'{self.document.symbol} - {self.title[:60]}'
