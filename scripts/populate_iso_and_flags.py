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

# Manual overrides for names that pycountry fuzzy-matches poorly,
# including historical/defunct countries and typos found in UN documents.
OVERRIDES = {
    # --- Current countries (name variants and typos) ---
    'Bolivia (Plurinational State of)': 'BOL',
    'Bolivian Republic of Venezuela': 'VEN',
    'China': 'CHN',
    'Congo': 'COG',
    'Côte d\'Ivoire': 'CIV',
    'Cote d\'Ivoire': 'CIV',
    "Côte D'Ivoire": 'CIV',
    "Cote d'lvoire": 'CIV',   # lowercase-L OCR typo
    "\\ Cote d'lvoire": 'CIV',  # with leading backslash
    'Czech Republic': 'CZE',
    'Czechia': 'CZE',
    'Democratic People\'s Republic of Korea': 'PRK',
    'Democratic People\u2019s Republic of Korea': 'PRK',  # curly apostrophe variant
    'Democratic Republic of Korea': 'PRK',   # erroneous but appears in old docs
    'Democratic Republic of the Congo': 'COD',
    'Demark': 'DNK',           # typo for Denmark
    'Egypt': 'EGY',
    'Arab Republic of Egypt': 'EGY',
    'Eswatini': 'SWZ',
    'Swaziland': 'SWZ',
    'Gambia': 'GMB',
    'The Gambia': 'GMB',
    'Guinea Bissau': 'GNB',    # missing hyphen
    'Guinea- Bissau': 'GNB',   # space-hyphen variant
    'Guinea-Bissau': 'GNB',
    'Holy See': 'VAT',
    'Iran': 'IRN',
    'Iran (Islamic Republic of)': 'IRN',
    'Islamic Republic of Iran': 'IRN',
    'Irag': 'IRQ',             # typo for Iraq
    'Iraq': 'IRQ',
    'Kazakstan': 'KAZ',        # old transliteration
    'Kazakhstan': 'KAZ',
    'Korea': 'KOR',
    'Republic of Korea': 'KOR',
    'Kosovo': 'XKX',
    'Kyrgyzstan': 'KGZ',
    'Kyrgyz Republic': 'KGZ',
    'Kyrzgystan': 'KGZ',       # typo
    'Laos': 'LAO',
    "Lao People's Democratic Republic": 'LAO',
    "Lao People\u2019s Democratic Republic": 'LAO',
    'Libya': 'LBY',
    'Libyan Arab Jamahiriya': 'LBY',
    'Libya Arab Jamahiriya': 'LBY',    # variant
    'Libyan Arab Jamahariya': 'LBY',   # typo
    'Lichtenstein': 'LIE',     # typo
    'Liechenstein': 'LIE',     # typo
    'Liechstenstein': 'LIE',   # typo
    'Liechtenstein': 'LIE',
    'Luxembourg': 'LUX',
    'Marshal Islands': 'MHL',  # missing 'l'
    'Micronesia': 'FSM',
    'Federated States of Micronesia': 'FSM',
    'Moldova': 'MDA',
    'Republic of Moldova': 'MDA',
    'Mozambigue': 'MOZ',       # typo
    'Mozambique': 'MOZ',
    'Netherlands': 'NLD',
    'Netherlands (Kingdom of the)': 'NLD',
    'North Korea': 'PRK',
    'North Macedonia': 'MKD',
    'Republic of North Macedonia': 'MKD',
    'The former Yugoslav Republic of Macedonia': 'MKD',
    'the Former Yugoslav Republic of Macedonia': 'MKD',
    'The Former Yugoslav Republic of Macedonia': 'MKD',
    'Palestine': 'PSE',
    'State of Palestine': 'PSE',
    'Observer State of Palestine': 'PSE',
    'Observer for Palestine': 'PSE',
    'People\'s Democratic Republic of Korea': 'PRK',
    'Russia': 'RUS',
    'Russian Federation': 'RUS',
    'The Russian Federation': 'RUS',
    'Sao Tome et Principe': 'STP',    # French variant
    'Sao Tome and Principe': 'STP',
    'São Tomé and Príncipe': 'STP',
    'Solomon Islands': 'SLB',
    'South Korea': 'KOR',
    'South Sudan': 'SSD',
    'Sri Lanka': 'LKA',
    'Sudan': 'SDN',
    'Suriname': 'SUR',
    'Sweden\xad': 'SWE',       # soft-hyphen suffix
    'Syria': 'SYR',
    'Syrian Arab Republic': 'SYR',
    'Syrian Arabic Republic': 'SYR',  # typo
    'Taiwan': 'TWN',
    'Tanzania': 'TZA',
    'United Republic of Tanzania': 'TZA',
    'the Bolivarian Republic of Venezuela': 'VEN',
    'the United Arab Emirates': 'ARE',
    'Timor-Leste': 'TLS',
    'East Timor': 'TLS',
    'Timor- Leste': 'TLS',     # space before hyphen variant
    'Tonga': 'TON',
    'Turkey': 'TUR',
    'Türkiye': 'TUR',
    'Tuvalu': 'TUV',
    'United Arab Emiraes': 'ARE',  # typo
    'United Kingdom': 'GBR',
    'United Kingdom of Great Britain and Northern Ireland': 'GBR',
    'United States': 'USA',
    'United States of America': 'USA',
    'Vanuatu': 'VUT',
    'Venezuela': 'VEN',
    'Venezuela (Bolivarian Republic of)': 'VEN',
    'Viet Nam': 'VNM',
    'Vietnam': 'VNM',
    'Yemen': 'YEM',
    'Austalia': 'AUS',         # typo in DB
    'Bahamas': 'BHS',
    'The Bahamas': 'BHS',
    'Cabo Verde': 'CPV',
    'Cape Verde': 'CPV',
    'Comoros': 'COM',
    'Marshall Islands': 'MHL',
    'Micronesia (Federated States of)': 'FSM',
    'Niger': 'NER',
    'Nigeria': 'NGA',
    'Palau': 'PLW',
    'Papua New Guinea': 'PNG',
    'Saint Kitts and Nevis': 'KNA',
    'Saint Lucia': 'LCA',
    'Saint Vincent and the Grenadines': 'VCT',
    'Samoa': 'WSM',
    'San Marino': 'SMR',

    # --- Historical / defunct countries (ISO 3166-3) ---
    # These no longer exist but appear in UN documents from 1945 onwards.
    'Yugoslavia': 'YUG',
    'Federal Republic of Yugoslavia': 'YUG',
    'Socialist Federal Republic of Yugoslavia': 'YUG',
    'USSR': 'SUN',
    'Soviet Union': 'SUN',
    'Union of Soviet Socialist Republics': 'SUN',
    'Czechoslovakia': 'CSK',
    'Czechoslovak Socialist Republic': 'CSK',
    'Czechoslovak Republic': 'CSK',
    'German Democratic Republic': 'DDR',
    'East Germany': 'DDR',
    'Serbia and Montenegro': 'SCG',
    'Zaire': 'ZAR',
    'Republic of Zaire': 'ZAR',
    'Netherlands Antilles': 'ANT',
    'Byelorussian SSR': 'BYS',
    'Byelorussian Soviet Socialist Republic': 'BYS',
    'Belorussian SSR': 'BYS',
    'Burma': 'BUR',
    'Socialist Republic of the Union of Burma': 'BUR',
    'Upper Volta': 'HVO',
    'Republic of Upper Volta': 'HVO',
    'Dahomey': 'DHY',
    'Republic of Dahomey': 'DHY',
    'South Yemen': 'YMD',
    "People's Democratic Republic of Yemen": 'YMD',
    'Democratic Yemen': 'YMD',
    'North Vietnam': 'VDR',
    'Viet-Nam, Democratic Republic of': 'VDR',
    'Democratic Republic of Viet-Nam': 'VDR',
    'Southern Rhodesia': 'RHO',
    'Rhodesia': 'RHO',
}

# ISO2 codes for historical countries not in pycountry.countries.
# Used only for flag downloads from flagcdn.com.
# Note: CSK (Czechoslovakia) and SCG (Serbia and Montenegro) both used
# the 'CS' alpha-2 code historically; flagcdn.com serves one flag for 'cs'.
HISTORICAL_ISO2 = {
    'YUG': 'YU',   # Yugoslavia
    'SUN': 'SU',   # USSR
    'CSK': 'CS',   # Czechoslovakia
    'DDR': 'DD',   # East Germany
    'ZAR': 'ZR',   # Zaire
    'ANT': 'AN',   # Netherlands Antilles
    'SCG': 'CS',   # Serbia and Montenegro (shares 'CS' with CSK)
    'VDR': 'VD',   # North Vietnam / Democratic Republic of Viet-Nam
    'YMD': 'YD',   # South Yemen / Democratic Yemen
    'HVO': 'HV',   # Upper Volta
    'DHY': 'DY',   # Dahomey
    'RHO': 'RH',   # Southern Rhodesia
    'BUR': 'BU',   # Burma
    'BYS': None,   # Byelorussian SSR — 'BY' is now Belarus; skip auto-download
}


def lookup_iso3(name):
    if name in OVERRIDES:
        return OVERRIDES[name]
    # Exact match (current countries)
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
    # Fuzzy match on current countries
    try:
        results = pycountry.countries.search_fuzzy(name)
        if results:
            return results[0].alpha_3
    except LookupError:
        pass
    # Exact match on historical/defunct countries (ISO 3166-3)
    hc = pycountry.historic_countries.get(name=name)
    if hc:
        return hc.alpha_3
    # Fuzzy match on historical countries
    try:
        results = pycountry.historic_countries.search_fuzzy(name)
        if results:
            return results[0].alpha_3
    except LookupError:
        pass
    return None


def get_iso2(iso3):
    """Return the ISO 3166-1 alpha-2 code for a given alpha-3 code.

    HISTORICAL_ISO2 takes priority so we can suppress or override codes
    where the historical alpha-2 collides with a current country (e.g. BYS/BY).
    Falls back to pycountry current countries, then pycountry historic countries.
    """
    if iso3 in HISTORICAL_ISO2:
        return HISTORICAL_ISO2[iso3]
    pc = pycountry.countries.get(alpha_3=iso3)
    if pc:
        return pc.alpha_2
    hc = pycountry.historic_countries.get(alpha_3=iso3)
    if hc:
        return getattr(hc, 'alpha_2', None)
    return None


# Wikimedia Commons fallback URLs for historical flags not on flagcdn.com.
# Verified via the Wikimedia Commons API (imageinfo endpoint).
WIKIMEDIA_FLAG_URLS = {
    'YUG': 'https://upload.wikimedia.org/wikipedia/commons/6/61/Flag_of_Yugoslavia_%281946-1992%29.svg',
    'CSK': 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Flag_of_the_Czech_Republic.svg',
    # Serbia and Montenegro shares iso2='CS' with Czechoslovakia; must use Wikimedia directly
    'SCG': 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Flag_of_Serbia_and_Montenegro_%281992%E2%80%932006%29.svg',
}


def download_flag(iso2, iso3):
    """Download SVG flag, saving as ISO3.svg.

    Tries flagcdn.com first (when iso2 is available); falls back to
    WIKIMEDIA_FLAG_URLS for historical countries whose codes are no longer
    served by flagcdn.com, or that share an iso2 with another country.
    """
    dest = os.path.join(FLAGS_DIR, f'{iso3}.svg')
    if os.path.exists(dest):
        return True
    urls = []
    if iso2:
        urls.append(f'https://flagcdn.com/{iso2.lower()}.svg')
    if iso3 in WIKIMEDIA_FLAG_URLS:
        urls.append(WIKIMEDIA_FLAG_URLS[iso3])
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'un-project/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            with open(dest, 'wb') as f:
                f.write(data)
            return True
        except Exception:
            continue
    print(f'  ✗ flag download failed for {iso2}/{iso3}')
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

        # Get iso2 (checks current countries, historic countries, and manual table)
        iso2 = get_iso2(iso3)

        # Update DB — iso3 and iso2 must both be UNIQUE across all rows.
        # Alias/typo entries may resolve to the same codes as a canonical entry;
        # in that case, skip iso2 (or both) gracefully rather than erroring out.
        iso3_changed = country.iso3 != iso3
        iso2_changed = iso2 and country.iso2 != iso2
        if iso3_changed or iso2_changed:
            try:
                Country.objects.filter(pk=country.pk).update(
                    iso3=iso3 if iso3_changed else country.iso3,
                    iso2=iso2 if iso2_changed else country.iso2,
                )
                country.iso3 = iso3
                if iso2_changed:
                    country.iso2 = iso2
            except Exception:
                # iso2 (or iso3) already owned by another row — try iso3 only
                if iso3_changed:
                    try:
                        Country.objects.filter(pk=country.pk).update(iso3=iso3)
                        country.iso3 = iso3
                        iso2 = None  # don't attempt flag download with conflicting iso2
                    except Exception:
                        iso2 = None  # iso3 also taken; flag will use existing file
                else:
                    iso2 = None

        # Download flag (also attempt when iso2 is absent but a Wikimedia URL exists)
        if iso2 or iso3 in WIKIMEDIA_FLAG_URLS:
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
