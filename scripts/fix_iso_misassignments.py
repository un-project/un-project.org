"""
Fix ISO3/ISO2 codes that were misassigned by populate_iso_and_flags.py
to garbled OCR country rows instead of the canonical rows.

Usage:
    python scripts/fix_iso_misassignments.py [--dry-run]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'un_site.settings')

import django
django.setup()

from django.db import transaction
from countries.models import Country

# (iso3, iso2, wrong_name, correct_name)
# wrong_name: the garbled DB row that currently holds the code
# correct_name: the canonical DB row that should hold the code
FIXES = [
    ('AND', 'AD', 'And',                                                     'Andorra'),
    ('ATG', 'AG', 'Antigua and Barbud',                                      'Antigua and Barbuda'),
    ('BRB', 'BB', 'BarbadoS',                                                'Barbados'),
    ('BFA', 'BF', 'Burkina',                                                 'Burkina Faso'),
    ('BDI', 'BI', 'Bujumbura',                                               'Burundi'),
    ('CUB', 'CU', 'CUba',                                                    'Cuba'),
    ('CYP', 'CY', 'CYPruS',                                                  'Cyprus'),
    ('DOM', 'DO', 'Dominican',                                               'Dominican Republic'),
    ('FRA', 'FR', 'Fran',                                                    'France'),
    ('GMB', 'GM', 'Ambia',                                                   'Gambia'),
    ('DEU', 'DE', 'Fedéral Republic of',                                     'Germany'),
    ('HTI', 'HT', 'Ait',                                                     'Haiti'),
    ('HUN', 'HU', 'Hung',                                                    'Hungary'),
    ('LTU', 'LT', 'LithuanIa',                                               'Lithuania'),
    ('MDG', 'MG', 'Anan',                                                    'Madagascar'),
    ('MWI', 'MW', 'ChînJ',                                                   'Malawi'),
    ('MRT', 'MR', 'Auritania',                                               'Mauritania'),
    ('MEX', 'MX', 'Mexi',                                                    'Mexico'),
    ('MMR', 'MM', 'Again',                                                   'Myanmar'),
    ('NGA', 'NG', 'NigeriA',                                                 'Nigeria'),
    ('OMN', 'OM', 'Man',                                                     'Oman'),
    ('PHL', 'PH', 'Gay',                                                     'Philippines'),
    ('RUS', 'RU', 'Republic',                                                'Russian Federation'),
    ('WSM', 'WS', 'Amoa',                                                    'Samoa'),
    ('STP', 'ST', 'Sao Tom',                                                 'Sao Tome and Principe'),
    ('SAU', 'SA', 'Saudi',                                                   'Saudi Arabia'),
    ('SLE', 'SL', 'Erra Leone',                                              'Sierra Leone'),
    ('SVN', 'SI', 'OJbA',                                                    'Slovenia'),
    ('ZAF', 'ZA', 'Africa',                                                  'South Africa'),
    ('LKA', 'LK', 'Democratic',                                              'Sri Lanka'),
    ('PSE', 'PS', 'Jerusalem',                                               'State of Palestine'),
    ('SDN', 'SD', 'Dan',                                                     'Sudan'),
    ('SWE', 'SE', 'Eden',                                                    'Sweden'),
    ('CHE', 'CH', 'Swiss',                                                   'Switzerland'),
    ('SYR', 'SY', 'Syrian',                                                  'Syrian Arab Republic'),
    ('TKM', 'TM', 'Gabat',                                                   'Turkmenistan'),
    ('UGA', 'UG', 'But',                                                     'Uganda'),
    ('UKR', 'UA', 'Sevastopol',                                              'Ukraine'),
    ('ARE', 'AE', 'Are',                                                     'United Arab Emirates'),
    ('GBR', 'GB', 'Borders',                                                 'United Kingdom of Great Britain and Northern Ireland'),
    ('TZA', 'TZ', 'Rogo',                                                    'United Republic of Tanzania'),
    ('VNM', 'VN', 'Social',                                                  'Viet Nam'),
    ('SUN', 'SU', 'Soviet Socialist Republics',                              'Union of Soviet Socialist Republics'),
    ('YUG', 'YU', 'Yugo',                                                    'Yugoslavia'),
]

dry_run = '--dry-run' in sys.argv

errors = []
fixed = []

with transaction.atomic():
    for iso3, iso2, wrong_name, correct_name in FIXES:
        # Verify the wrong row exists with this iso3
        try:
            wrong = Country.objects.get(name=wrong_name, iso3=iso3)
        except Country.DoesNotExist:
            errors.append(f'  SKIP {iso3}: wrong row "{wrong_name}" not found with iso3={iso3}')
            continue
        except Country.MultipleObjectsReturned:
            errors.append(f'  ERROR {iso3}: multiple rows with name="{wrong_name}" and iso3={iso3}')
            continue

        # Verify the correct row exists without an iso3
        try:
            correct = Country.objects.get(name=correct_name)
        except Country.DoesNotExist:
            errors.append(f'  ERROR {iso3}: correct row "{correct_name}" not found')
            continue
        except Country.MultipleObjectsReturned:
            errors.append(f'  ERROR {iso3}: multiple rows with name="{correct_name}"')
            continue

        if correct.iso3 and correct.iso3 != iso3:
            errors.append(
                f'  SKIP {iso3}: correct row "{correct_name}" already has iso3={correct.iso3}'
            )
            continue

        # All clear — perform the swap
        if not dry_run:
            # Clear wrong row first (releases the unique slots)
            Country.objects.filter(pk=wrong.pk).update(iso3=None, iso2=None)
            # Assign to correct row
            Country.objects.filter(pk=correct.pk).update(iso3=iso3, iso2=iso2)

        fixed.append(
            f'  {"[DRY]" if dry_run else "✓"} {iso3}/{iso2}: "{wrong_name}" → "{correct_name}"'
        )

    if dry_run:
        transaction.set_rollback(True)

for line in fixed:
    print(line)
if errors:
    print()
    for line in errors:
        print(line)

print(f'\n{"[DRY RUN] " if dry_run else ""}Fixed {len(fixed)} assignments, {len(errors)} issues.')
