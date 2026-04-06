from django.db import migrations


class Migration(migrations.Migration):
    """Register pre-existing vetoes and veto_countries tables (managed=False)."""

    dependencies = [
        ('votes', '0002_initial'),
    ]

    operations = []
