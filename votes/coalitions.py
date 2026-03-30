# Named political blocs used to display aggregate voting patterns on the votes page.
# ISO 3166-1 alpha-3 codes; any code absent from the database is silently skipped.

COALITIONS = [
    # ── UN Security Council ──────────────────────────────────────────────────
    {
        'name': 'P5',
        'slug': 'p5',
        'label': 'UN Security Council Permanent Members',
        'iso3': ['CHN', 'FRA', 'GBR', 'RUS', 'USA'],
    },

    # ── Major political groupings ────────────────────────────────────────────
    {
        'name': 'G77',
        'slug': 'g77',
        'label': 'Group of 77 (developing nations coalition, 134 members)',
        'iso3': [
            'AFG', 'DZA', 'AGO', 'ATG', 'ARG', 'AZE', 'BHS', 'BHR', 'BGD',
            'BRB', 'BLZ', 'BEN', 'BTN', 'BOL', 'BIH', 'BWA', 'BRA', 'BRN',
            'BFA', 'BDI', 'CPV', 'KHM', 'CMR', 'CAF', 'TCD', 'CHL', 'CHN',
            'COL', 'COM', 'COG', 'COD', 'CRI', 'CUB', 'DJI', 'DMA', 'DOM',
            'ECU', 'EGY', 'SLV', 'GNQ', 'ERI', 'SWZ', 'ETH', 'FJI', 'GAB',
            'GMB', 'GHA', 'GRD', 'GTM', 'GIN', 'GNB', 'GUY', 'HTI', 'HND',
            'IND', 'IDN', 'IRN', 'IRQ', 'JAM', 'JOR', 'KEN', 'KIR', 'PRK',
            'KWT', 'LAO', 'LBN', 'LSO', 'LBR', 'LBY', 'MDG', 'MWI', 'MYS',
            'MDV', 'MLI', 'MHL', 'MRT', 'MUS', 'FSM', 'MAR', 'MOZ', 'MMR',
            'NAM', 'NRU', 'NPL', 'NIC', 'NER', 'NGA', 'OMN', 'PAK', 'PLW',
            'PSE', 'PAN', 'PNG', 'PRY', 'PER', 'PHL', 'QAT', 'RWA', 'KNA',
            'LCA', 'VCT', 'WSM', 'STP', 'SAU', 'SEN', 'SLE', 'SLB', 'SOM',
            'ZAF', 'SSD', 'SDN', 'SUR', 'SYR', 'TJK', 'TZA', 'THA', 'TLS',
            'TGO', 'TON', 'TTO', 'TUN', 'TKM', 'TUV', 'UGA', 'ARE', 'URY',
            'UZB', 'VUT', 'VEN', 'VNM', 'YEM', 'ZMB', 'ZWE',
        ],
    },
    {
        'name': 'NAM',
        'slug': 'nam',
        'label': 'Non-Aligned Movement (120 member states)',
        'iso3': [
            'AFG', 'DZA', 'AGO', 'ATG', 'AZE', 'BHS', 'BHR', 'BGD', 'BRB',
            'BLZ', 'BEN', 'BTN', 'BOL', 'BWA', 'BRN', 'BFA', 'BDI', 'CPV',
            'KHM', 'CMR', 'CAF', 'TCD', 'CHL', 'COL', 'COM', 'COG', 'COD',
            'CRI', 'CIV', 'CUB', 'DJI', 'DMA', 'DOM', 'ECU', 'EGY', 'SLV',
            'GNQ', 'ERI', 'SWZ', 'ETH', 'FJI', 'GAB', 'GMB', 'GHA', 'GRD',
            'GTM', 'GIN', 'GNB', 'GUY', 'HTI', 'HND', 'IND', 'IDN', 'IRN',
            'IRQ', 'JAM', 'JOR', 'KEN', 'KWT', 'LAO', 'LBN', 'LSO', 'LBR',
            'LBY', 'MDG', 'MWI', 'MYS', 'MDV', 'MLI', 'MRT', 'MUS', 'MAR',
            'MOZ', 'MMR', 'NAM', 'NPL', 'NIC', 'NER', 'NGA', 'OMN', 'PAK',
            'PSE', 'PAN', 'PNG', 'PRY', 'PER', 'PHL', 'QAT', 'RWA', 'KNA',
            'LCA', 'VCT', 'STP', 'SAU', 'SEN', 'SLE', 'SLB', 'SOM', 'ZAF',
            'SSD', 'SDN', 'SUR', 'SYR', 'TJK', 'TZA', 'THA', 'TLS', 'TGO',
            'TTO', 'TUN', 'TKM', 'UGA', 'ARE', 'UZB', 'VUT', 'VEN', 'VNM',
            'YEM', 'ZMB', 'ZWE',
        ],
    },
    {
        'name': 'BRICS+',
        'slug': 'brics-plus',
        'label': 'BRICS+ (expanded group from 2024)',
        'iso3': ['BRA', 'CHN', 'IND', 'RUS', 'ZAF', 'EGY', 'ETH', 'IRN', 'SAU', 'ARE'],
    },
    {
        'name': 'BRICS',
        'slug': 'brics',
        'label': 'BRICS original (Brazil, Russia, India, China, South Africa)',
        'iso3': ['BRA', 'CHN', 'IND', 'RUS', 'ZAF'],
    },

    # ── Western alliances ────────────────────────────────────────────────────
    {
        'name': 'NATO',
        'slug': 'nato',
        'label': 'NATO (32 member states)',
        'iso3': [
            'ALB', 'BEL', 'BGR', 'CAN', 'HRV', 'CZE', 'DNK', 'EST', 'FIN',
            'FRA', 'DEU', 'GRC', 'HUN', 'ISL', 'ITA', 'LVA', 'LTU', 'LUX',
            'MNE', 'NLD', 'MKD', 'NOR', 'POL', 'PRT', 'ROU', 'SVK', 'SVN',
            'ESP', 'SWE', 'TUR', 'GBR', 'USA',
        ],
    },
    {
        'name': 'EU',
        'slug': 'eu',
        'label': 'European Union (27 members)',
        'iso3': [
            'AUT', 'BEL', 'BGR', 'CYP', 'CZE', 'DEU', 'DNK', 'EST', 'ESP',
            'FIN', 'FRA', 'GRC', 'HRV', 'HUN', 'IRL', 'ITA', 'LTU', 'LUX',
            'LVA', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'SWE',
        ],
    },
    {
        'name': 'OSCE',
        'slug': 'osce',
        'label': 'Organisation for Security and Co-operation in Europe (57 members)',
        'iso3': [
            'ALB', 'AND', 'ARM', 'AUT', 'AZE', 'BLR', 'BEL', 'BIH', 'BGR',
            'CAN', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'GEO',
            'DEU', 'GRC', 'HUN', 'ISL', 'IRL', 'ITA', 'KAZ', 'KGZ', 'LVA',
            'LIE', 'LTU', 'LUX', 'MLT', 'MDA', 'MCO', 'MNE', 'NLD', 'MKD',
            'NOR', 'POL', 'PRT', 'ROU', 'RUS', 'SMR', 'SRB', 'SVK', 'SVN',
            'ESP', 'SWE', 'CHE', 'TJK', 'TUR', 'TKM', 'UKR', 'GBR', 'USA',
            'UZB',
        ],
    },
    {
        'name': 'Council of Europe',
        'slug': 'council-of-europe',
        'label': 'Council of Europe (46 members)',
        'iso3': [
            'ALB', 'AND', 'ARM', 'AUT', 'AZE', 'BEL', 'BIH', 'BGR', 'HRV',
            'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'GEO', 'DEU', 'GRC',
            'HUN', 'ISL', 'IRL', 'ITA', 'LVA', 'LIE', 'LTU', 'LUX', 'MLT',
            'MDA', 'MCO', 'MNE', 'NLD', 'MKD', 'NOR', 'POL', 'PRT', 'ROU',
            'SMR', 'SRB', 'SVK', 'SVN', 'ESP', 'SWE', 'CHE', 'TUR', 'UKR',
            'GBR',
        ],
    },

    # ── UN Regional Groups ───────────────────────────────────────────────────
    {
        'name': 'African Group',
        'slug': 'african-group',
        'label': 'UN African Group (54 member states)',
        'iso3': [
            'DZA', 'AGO', 'BEN', 'BWA', 'BFA', 'BDI', 'CMR', 'CPV', 'CAF',
            'TCD', 'COM', 'COD', 'COG', 'CIV', 'DJI', 'EGY', 'GNQ', 'ERI',
            'SWZ', 'ETH', 'GAB', 'GMB', 'GHA', 'GIN', 'GNB', 'KEN', 'LSO',
            'LBR', 'LBY', 'MDG', 'MWI', 'MLI', 'MRT', 'MUS', 'MAR', 'MOZ',
            'NAM', 'NER', 'NGA', 'RWA', 'STP', 'SEN', 'SLE', 'SOM', 'ZAF',
            'SSD', 'SDN', 'TZA', 'TGO', 'TUN', 'UGA', 'ZMB', 'ZWE',
        ],
    },
    {
        'name': 'Arab Group',
        'slug': 'arab-group',
        'label': 'UN Arab Group / League of Arab States (22 members)',
        'iso3': [
            'DZA', 'BHR', 'COM', 'DJI', 'EGY', 'IRQ', 'JOR', 'KWT', 'LBN',
            'LBY', 'MRT', 'MAR', 'OMN', 'PSE', 'QAT', 'SAU', 'SOM', 'SDN',
            'SYR', 'TUN', 'ARE', 'YEM',
        ],
    },
    {
        'name': 'Asia-Pacific Group',
        'slug': 'asia-pacific-group',
        'label': 'UN Asia-Pacific Group (53 members)',
        'iso3': [
            'AFG', 'ARM', 'AUS', 'AZE', 'BHR', 'BGD', 'BTN', 'BRN', 'KHM',
            'CHN', 'CYP', 'PRK', 'FJI', 'GEO', 'IND', 'IDN', 'IRN', 'IRQ',
            'ISR', 'JPN', 'JOR', 'KAZ', 'KIR', 'KWT', 'KGZ', 'LAO', 'LBN',
            'MYS', 'MDV', 'MHL', 'FSM', 'MNG', 'MMR', 'NRU', 'NPL', 'NZL',
            'OMN', 'PAK', 'PLW', 'PNG', 'PHL', 'QAT', 'KOR', 'SAU', 'SGP',
            'SLB', 'LKA', 'SYR', 'TJK', 'THA', 'TLS', 'TON', 'TKM', 'TUV',
            'ARE', 'UZB', 'VUT', 'VNM', 'YEM',
        ],
    },
    {
        'name': 'GRULAC',
        'slug': 'grulac',
        'label': 'UN Latin America & Caribbean Group (33 members)',
        'iso3': [
            'ATG', 'ARG', 'BHS', 'BRB', 'BLZ', 'BOL', 'BRA', 'CHL', 'COL',
            'CRI', 'CUB', 'DMA', 'DOM', 'ECU', 'SLV', 'GRD', 'GTM', 'GUY',
            'HTI', 'HND', 'JAM', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'KNA',
            'LCA', 'VCT', 'SUR', 'TTO', 'URY', 'VEN',
        ],
    },
    {
        'name': 'WEOG',
        'slug': 'weog',
        'label': 'UN Western European & Others Group (29 members)',
        'iso3': [
            'AND', 'AUS', 'AUT', 'BEL', 'CAN', 'DNK', 'FIN', 'FRA', 'DEU',
            'GRC', 'ISL', 'IRL', 'ISR', 'ITA', 'LIE', 'LUX', 'MLT', 'MCO',
            'NLD', 'NZL', 'NOR', 'PRT', 'SMR', 'ESP', 'SWE', 'CHE', 'TUR',
            'GBR', 'USA',
        ],
    },
    {
        'name': 'EAEG',
        'slug': 'eaeg',
        'label': 'UN Eastern European Group (23 members)',
        'iso3': [
            'ALB', 'ARM', 'AZE', 'BLR', 'BIH', 'BGR', 'HRV', 'CZE', 'EST',
            'GEO', 'HUN', 'KAZ', 'KGZ', 'LVA', 'LTU', 'MDA', 'MNE', 'MKD',
            'POL', 'ROU', 'RUS', 'SRB', 'SVK', 'SVN', 'TJK', 'TKM', 'UKR',
            'UZB',
        ],
    },

    # ── Economic groups ──────────────────────────────────────────────────────
    {
        'name': 'G20',
        'slug': 'g20',
        'label': 'G20 (major economies)',
        'iso3': [
            'ARG', 'AUS', 'BRA', 'CAN', 'CHN', 'FRA', 'DEU', 'IND', 'IDN',
            'ITA', 'JPN', 'KOR', 'MEX', 'RUS', 'SAU', 'ZAF', 'TUR', 'GBR',
            'USA',
        ],
    },
    {
        'name': 'OPEC',
        'slug': 'opec',
        'label': 'OPEC (13 member states)',
        'iso3': ['DZA', 'COG', 'GAB', 'GNQ', 'IRN', 'IRQ', 'KWT', 'LBY', 'NGA', 'SAU', 'ARE', 'VEN'],
    },

    # ── Regional / thematic groups ───────────────────────────────────────────
    {
        'name': 'ASEAN',
        'slug': 'asean',
        'label': 'Association of Southeast Asian Nations (10 members)',
        'iso3': ['BRN', 'KHM', 'IDN', 'LAO', 'MYS', 'MMR', 'PHL', 'SGP', 'THA', 'VNM'],
    },
    {
        'name': 'OIC',
        'slug': 'oic',
        'label': 'Organisation of Islamic Cooperation (57 members)',
        'iso3': [
            'AFG', 'ALB', 'DZA', 'AZE', 'BHR', 'BGD', 'BEN', 'BRN', 'BFA',
            'CMR', 'CAF', 'TCD', 'COM', 'DJI', 'EGY', 'GAB', 'GMB', 'GIN',
            'GNB', 'GUY', 'IDN', 'IRN', 'IRQ', 'JOR', 'KAZ', 'KWT', 'KGZ',
            'LBN', 'LBY', 'MYS', 'MDV', 'MLI', 'MRT', 'MAR', 'MOZ', 'NER',
            'NGA', 'OMN', 'PAK', 'PSE', 'QAT', 'SAU', 'SEN', 'SLE', 'SOM',
            'SDN', 'SUR', 'SYR', 'TJK', 'TGO', 'TUN', 'TUR', 'TKM', 'UGA',
            'ARE', 'UZB', 'YEM',
        ],
    },
    {
        'name': 'IBSA',
        'slug': 'ibsa',
        'label': 'IBSA Dialogue Forum (India, Brazil, South Africa)',
        'iso3': ['IND', 'BRA', 'ZAF'],
    },
    {
        'name': 'BASIC',
        'slug': 'basic',
        'label': 'BASIC (climate negotiating bloc: Brazil, South Africa, India, China)',
        'iso3': ['BRA', 'ZAF', 'IND', 'CHN'],
    },
    {
        'name': 'CARICOM',
        'slug': 'caricom',
        'label': 'Caribbean Community (15 members)',
        'iso3': ['ATG', 'BHS', 'BRB', 'BLZ', 'DMA', 'GRD', 'GUY', 'HTI', 'JAM', 'KNA', 'LCA', 'SUR', 'TTO', 'VCT'],
    },
    {
        'name': 'Pacific Islands',
        'slug': 'pacific-islands',
        'label': 'Pacific Islands Forum (18 members)',
        'iso3': ['AUS', 'COK', 'FJI', 'KIR', 'MHL', 'FSM', 'NRU', 'NZL', 'NIU', 'PLW', 'PNG', 'WSM', 'SLB', 'TON', 'TUV', 'VUT'],
    },
]

COALITIONS_BY_SLUG = {c['slug']: c for c in COALITIONS}
