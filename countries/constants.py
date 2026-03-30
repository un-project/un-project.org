# ISO 3166-1 alpha-3 codes of states that no longer exist.
# Any country in the DB whose iso3 is NOT in this set is treated as current.
# This is easier to maintain correctly than listing all ~200 current states.
HISTORICAL_ISO3 = frozenset([
    'SUN',  # Soviet Union (USSR)
    'DDR',  # East Germany
    'GER',  # West Germany (pre-reunification)
    'CSK',  # Czechoslovakia
    'YUG',  # Yugoslavia (SFRY)
    'SCG',  # Serbia and Montenegro
    'YMD',  # South Yemen (PDRY)
    'EAT',  # Tanganyika
    'EAZ',  # Zanzibar
    'HVO',  # Upper Volta (now Burkina Faso)
    'BYS',  # Byelorussian SSR (voted separately in the UN)
])
