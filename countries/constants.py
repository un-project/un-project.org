# ISO 3166-1 alpha-3 codes of states that no longer exist.
# Any country in the DB whose iso3 is NOT in this set is treated as current.
# This is easier to maintain correctly than listing all ~200 current states.
HISTORICAL_ISO3 = frozenset([
    'SUN',  # Soviet Union (USSR)
    'DDR',  # East Germany
    'GER',  # West Germany (pre-reunification, legacy code — DB uses DEU)
    'DEU',  # Federal Republic of Germany in DB (pre-reunification West Germany entry)
    'CSK',  # Czechoslovakia
    'YUG',  # Yugoslavia (SFRY)
    'SCG',  # Serbia and Montenegro
    'YMD',  # South Yemen (PDRY)
    'EAT',  # Tanganyika
    'EAZ',  # Zanzibar
    'HVO',  # Upper Volta (now Burkina Faso)
    'BYS',  # Byelorussian SSR (voted separately in the UN)
])

# Contextual info for each historical state.
# successors: list of (display_name, iso3) — iso3 may be None for unrecognised states.
HISTORICAL_INFO = {
    'SUN': {
        'dissolved': 1991,
        'note': 'The Soviet Union (USSR) dissolved in December 1991, ending 69 years as a state. Russia was recognised as the continuing state for UN purposes.',
        'successors': [
            ('Russia', 'RUS'), ('Ukraine', 'UKR'), ('Belarus', 'BLR'),
            ('Estonia', 'EST'), ('Latvia', 'LVA'), ('Lithuania', 'LTU'),
            ('Moldova', 'MDA'), ('Georgia', 'GEO'), ('Armenia', 'ARM'),
            ('Azerbaijan', 'AZE'), ('Kazakhstan', 'KAZ'), ('Uzbekistan', 'UZB'),
            ('Turkmenistan', 'TKM'), ('Tajikistan', 'TJK'), ('Kyrgyzstan', 'KGZ'),
        ],
    },
    'DDR': {
        'dissolved': 1990,
        'note': 'East Germany (German Democratic Republic) was absorbed into the Federal Republic of Germany on 3 October 1990 following German reunification.',
        'successors': [('Germany', None)],
    },
    'DEU': {
        'dissolved': 1990,
        'note': 'The Federal Republic of Germany (West Germany) formally unified with East Germany on 3 October 1990. The reunified Federal Republic of Germany continued the FRG\'s United Nations membership.',
        'successors': [('Germany', None)],
    },
    'GER': {
        'dissolved': 1990,
        'note': 'West Germany (Federal Republic of Germany) formally unified with East Germany on 3 October 1990 to form the reunified Federal Republic of Germany.',
        'successors': [('Germany', None)],
    },
    'CSK': {
        'dissolved': 1993,
        'note': 'Czechoslovakia peacefully dissolved on 1 January 1993 in the "Velvet Divorce", splitting into two independent states.',
        'successors': [('Czech Republic', 'CZE'), ('Slovakia', 'SVK')],
    },
    'YUG': {
        'dissolved': 1992,
        'note': 'The Socialist Federal Republic of Yugoslavia began dissolving in 1991–92 following declarations of independence by its constituent republics.',
        'successors': [
            ('Slovenia', 'SVN'), ('Croatia', 'HRV'), ('Bosnia & Herzegovina', 'BIH'),
            ('Serbia', 'SRB'), ('Montenegro', 'MNE'), ('North Macedonia', 'MKD'),
        ],
    },
    'SCG': {
        'dissolved': 2006,
        'note': 'Serbia and Montenegro (formerly the Federal Republic of Yugoslavia) dissolved on 3 June 2006 after Montenegro voted for independence.',
        'successors': [('Serbia', 'SRB'), ('Montenegro', 'MNE')],
    },
    'YMD': {
        'dissolved': 1990,
        'note': "The People's Democratic Republic of Yemen (South Yemen) unified with North Yemen on 22 May 1990 to form the Republic of Yemen.",
        'successors': [('Yemen', 'YEM')],
    },
    'EAT': {
        'dissolved': 1964,
        'note': 'Tanganyika merged with the island of Zanzibar on 26 April 1964 to form the United Republic of Tanzania.',
        'successors': [('Tanzania', 'TZA')],
    },
    'EAZ': {
        'dissolved': 1964,
        'note': 'Zanzibar merged with Tanganyika on 26 April 1964 to form the United Republic of Tanzania.',
        'successors': [('Tanzania', 'TZA')],
    },
    'HVO': {
        'dissolved': 1984,
        'note': 'Upper Volta renamed itself Burkina Faso on 4 August 1984 under President Thomas Sankara. The state and its UN membership continued uninterrupted.',
        'successors': [('Burkina Faso', 'BFA')],
    },
    'BYS': {
        'dissolved': 1991,
        'note': 'The Byelorussian SSR was a constituent republic of the Soviet Union but held a separate UN seat from 1945. It became the independent Republic of Belarus in 1991.',
        'successors': [('Belarus', 'BLR')],
    },
}
