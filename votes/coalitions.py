# Named political blocs used to display aggregate voting patterns on the votes page.
# ISO 3166-1 alpha-3 codes; any code absent from the database is silently skipped.

COALITIONS = [
    {
        'name': 'P5',
        'label': 'UN Security Council Permanent Members',
        'iso3': ['CHN', 'FRA', 'GBR', 'RUS', 'USA'],
    },
    {
        'name': 'EU',
        'label': 'European Union (27 members)',
        'iso3': ['AUT', 'BEL', 'BGR', 'CYP', 'CZE', 'DEU', 'DNK', 'EST', 'ESP',
                 'FIN', 'FRA', 'GRC', 'HRV', 'HUN', 'IRL', 'ITA', 'LTU', 'LUX',
                 'LVA', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'SWE'],
    },
    {
        'name': 'BRICS',
        'label': 'Brazil, Russia, India, China, South Africa',
        'iso3': ['BRA', 'CHN', 'IND', 'RUS', 'ZAF'],
    },
    {
        'name': 'Arab Group',
        'label': 'League of Arab States (22 members)',
        'iso3': ['DZA', 'BHR', 'COM', 'DJI', 'EGY', 'IRQ', 'JOR', 'KWT', 'LBN',
                 'LBY', 'MRT', 'MAR', 'OMN', 'PSE', 'QAT', 'SAU', 'SOM', 'SDN',
                 'SYR', 'TUN', 'ARE', 'YEM'],
    },
    {
        'name': 'African Group',
        'label': 'African Union (54 member states)',
        'iso3': ['DZA', 'AGO', 'BEN', 'BWA', 'BFA', 'BDI', 'CMR', 'CPV', 'CAF',
                 'TCD', 'COM', 'COD', 'COG', 'CIV', 'DJI', 'EGY', 'GNQ', 'ERI',
                 'SWZ', 'ETH', 'GAB', 'GMB', 'GHA', 'GIN', 'GNB', 'KEN', 'LSO',
                 'LBR', 'LBY', 'MDG', 'MWI', 'MLI', 'MRT', 'MUS', 'MAR', 'MOZ',
                 'NAM', 'NER', 'NGA', 'RWA', 'STP', 'SEN', 'SLE', 'SOM', 'ZAF',
                 'SSD', 'SDN', 'TZA', 'TGO', 'TUN', 'UGA', 'ZMB', 'ZWE'],
    },
]
