"""
Populate iso2/iso3 on the countries table and download SVG flags.

Usage:
    python scripts/populate_iso_and_flags.py
"""
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'un_site.settings')

import django
django.setup()

import pycountry
from countries.models import Country

FLAGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'static', 'flags')
os.makedirs(FLAGS_DIR, exist_ok=True)

# Manual overrides for names that pycountry fuzzy-matches poorly
OVERRIDES = {
    'Bolivia (Plurinational State of)': 'BOL',
    'China': 'CHN',
    'Congo': 'COG',
    'Côte d\'Ivoire': 'CIV',
    'Cote d\'Ivoire': 'CIV',
    "Côte D'Ivoire": 'CIV',
    'Czech Republic': 'CZE',
    'Czechia': 'CZE',
    'Democratic People\'s Republic of Korea': 'PRK',
    'Democratic Republic of the Congo': 'COD',
    'Egypt': 'EGY',
    'Arab Republic of Egypt': 'EGY',
    'Eswatini': 'SWZ',
    'Swaziland': 'SWZ',
    'Gambia': 'GMB',
    'The Gambia': 'GMB',
    'Holy See': 'VAT',
    'Iran': 'IRN',
    'Iran (Islamic Republic of)': 'IRN',
    'Islamic Republic of Iran': 'IRN',
    'Korea': 'KOR',
    'Republic of Korea': 'KOR',
    'Kosovo': 'XKX',
    'Kyrgyzstan': 'KGZ',
    'Kyrgyz Republic': 'KGZ',
    'Laos': 'LAO',
    "Lao People's Democratic Republic": 'LAO',
    'Libya': 'LBY',
    'Libyan Arab Jamahiriya': 'LBY',
    'Micronesia': 'FSM',
    'Federated States of Micronesia': 'FSM',
    'Moldova': 'MDA',
    'Republic of Moldova': 'MDA',
    'North Korea': 'PRK',
    'North Macedonia': 'MKD',
    'Republic of North Macedonia': 'MKD',
    'The former Yugoslav Republic of Macedonia': 'MKD',
    'Palestine': 'PSE',
    'State of Palestine': 'PSE',
    'Russia': 'RUS',
    'Russian Federation': 'RUS',
    'South Korea': 'KOR',
    'Syria': 'SYR',
    'Syrian Arab Republic': 'SYR',
    'Taiwan': 'TWN',
    'Tanzania': 'TZA',
    'United Republic of Tanzania': 'TZA',
    'Timor-Leste': 'TLS',
    'East Timor': 'TLS',
    'Turkey': 'TUR',
    'Türkiye': 'TUR',
    'United Kingdom': 'GBR',
    'United Kingdom of Great Britain and Northern Ireland': 'GBR',
    'United States': 'USA',
    'United States of America': 'USA',
    'Venezuela': 'VEN',
    'Venezuela (Bolivarian Republic of)': 'VEN',
    'Viet Nam': 'VNM',
    'Vietnam': 'VNM',
    'Yemen': 'YEM',
    'Austalia': 'AUS',  # typo in DB
    'Bahamas': 'BHS',
    'The Bahamas': 'BHS',
    'Cabo Verde': 'CPV',
    'Cape Verde': 'CPV',
    'Comoros': 'COM',
    'Marshall Islands': 'MHL',
    'Micronesia (Federated States of)': 'FSM',
    'Netherlands': 'NLD',
    'Niger': 'NER',
    'Nigeria': 'NGA',
    'Palau': 'PLW',
    'Papua New Guinea': 'PNG',
    'Saint Kitts and Nevis': 'KNA',
    'Saint Lucia': 'LCA',
    'Saint Vincent and the Grenadines': 'VCT',
    'Samoa': 'WSM',
    'San Marino': 'SMR',
    'Sao Tome and Principe': 'STP',
    'São Tomé and Príncipe': 'STP',
    'Solomon Islands': 'SLB',
    'South Sudan': 'SSD',
    'Sri Lanka': 'LKA',
    'Sudan': 'SDN',
    'Suriname': 'SUR',
    'Tonga': 'TON',
    'Tuvalu': 'TUV',
    'Vanuatu': 'VUT',
}


def lookup_iso3(name):
    if name in OVERRIDES:
        return OVERRIDES[name]
    # Exact match
    c = pycountry.countries.get(name=name)
    if c:
        return c.alpha_3
    # Common name match
    c = pycountry.countries.get(common_name=name)
    if c:
        return c.alpha_3
    # Official name match
    c = pycountry.countries.get(official_name=name)
    if c:
        return c.alpha_3
    # Fuzzy match (returns list sorted by score)
    try:
        results = pycountry.countries.search_fuzzy(name)
        if results:
            return results[0].alpha_3
    except LookupError:
        pass
    return None


def download_flag(iso2, iso3):
    """Download SVG flag from flagcdn.com by ISO2, save as ISO3.svg."""
    dest = os.path.join(FLAGS_DIR, f'{iso3}.svg')
    if os.path.exists(dest):
        return True
    url = f'https://flagcdn.com/{iso2.lower()}.svg'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'un-project/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        with open(dest, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f'  ✗ flag download failed for {iso2}/{iso3}: {e}')
        return False


def main():
    countries = Country.objects.order_by('name')
    matched = 0
    skipped = 0
    no_match = []

    print(f'Processing {countries.count()} countries...\n')

    for country in countries:
        iso3 = lookup_iso3(country.name)
        if not iso3:
            skipped += 1
            no_match.append(country.name)
            continue

        # Get the pycountry entry to get iso2
        pc = pycountry.countries.get(alpha_3=iso3)
        if not pc:
            # Kosovo and a few others aren't in pycountry
            iso2 = None
        else:
            iso2 = pc.alpha_2

        # Update DB
        changed = False
        if country.iso3 != iso3:
            country.iso3 = iso3
            changed = True
        if iso2 and country.iso2 != iso2:
            country.iso2 = iso2
            changed = True
        if changed:
            try:
                Country.objects.filter(pk=country.pk).update(iso2=country.iso2, iso3=country.iso3)
            except Exception as e:
                print(f'  DB update failed for {country.name}: {e}')
                continue

        # Download flag
        if iso2:
            ok = download_flag(iso2, iso3)
            status = '✓' if ok else '!'
        else:
            status = '~'

        print(f'  {status} {country.name} → {iso3} ({iso2 or "no iso2"})')
        matched += 1
        time.sleep(0.05)  # be polite to flagcdn.com

    print(f'\nDone: {matched} matched, {skipped} skipped (not UN member states)')
    if no_match:
        print(f'\nNo ISO match for {len(no_match)} entries:')
        for name in no_match:
            print(f'  - {name}')


if __name__ == '__main__':
    main()
