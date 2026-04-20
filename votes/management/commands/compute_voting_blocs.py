"""
Compute data-driven voting blocs via connected-component clustering.

For each calendar year, build a 5-year rolling window of country_votes,
compute pairwise agreement rates, and group countries whose agreement
exceeds a threshold.  Results land in the voting_blocs table.

Usage:
    python manage.py compute_voting_blocs              # all years
    python manage.py compute_voting_blocs --year 2022  # single year
    python manage.py compute_voting_blocs --year-from 2010 --year-to 2023
    python manage.py compute_voting_blocs --threshold 0.80 --min-shared 25
"""

from django.core.management.base import BaseCommand
from django.db import connection


WINDOW_HALF   = 2      # window = [year-2, year+2]
DEFAULT_THRESH = 0.75  # agreement fraction to place countries in same bloc
DEFAULT_MIN    = 30    # minimum shared votes required


class Command(BaseCommand):
    help = 'Compute data-driven voting blocs from pairwise agreement clustering'

    def add_arguments(self, parser):
        parser.add_argument('--year',      type=int)
        parser.add_argument('--year-from', type=int, dest='year_from')
        parser.add_argument('--year-to',   type=int, dest='year_to')
        parser.add_argument('--threshold', type=float, default=DEFAULT_THRESH,
                            help='Agreement fraction threshold (default 0.75)')
        parser.add_argument('--min-shared', type=int, default=DEFAULT_MIN,
                            dest='min_shared',
                            help='Minimum shared votes per country pair (default 30)')

    def handle(self, *args, **options):
        threshold  = options['threshold']
        min_shared = options['min_shared']

        with connection.cursor() as cur:
            if options['year']:
                years = [options['year']]
            else:
                cur.execute("""
                    SELECT DISTINCT EXTRACT(YEAR FROM d.date)::int
                    FROM   country_votes cv
                    JOIN   votes v  ON v.id  = cv.vote_id
                    JOIN   documents d ON d.id = v.document_id
                    WHERE  d.date IS NOT NULL
                      AND  EXTRACT(YEAR FROM d.date) > 1900
                    ORDER  BY 1
                """)
                years = [r[0] for r in cur.fetchall()]
                if options['year_from']:
                    years = [y for y in years if y >= options['year_from']]
                if options['year_to']:
                    years = [y for y in years if y <= options['year_to']]

        self.stdout.write(f'Computing blocs for {len(years)} year(s) '
                          f'(threshold={threshold}, min_shared={min_shared})')

        for year in years:
            self._process_year(year, threshold, min_shared)

        self.stdout.write(self.style.SUCCESS('Done.'))

    def _process_year(self, year, threshold, min_shared):
        win_start = year - WINDOW_HALF
        win_end   = year + WINDOW_HALF

        with connection.cursor() as cur:
            # Pairwise agreement within the window — only recorded GA votes to
            # reduce noise (SC has far fewer votes and skews results).
            cur.execute("""
                SELECT cv1.country_id,
                       cv2.country_id,
                       SUM(CASE WHEN cv1.vote_position = cv2.vote_position
                                THEN 1 ELSE 0 END)::float / COUNT(*) AS agree,
                       COUNT(*) AS shared
                FROM   country_votes cv1
                JOIN   country_votes cv2
                    ON cv1.vote_id = cv2.vote_id
                   AND cv1.country_id < cv2.country_id
                JOIN   votes v  ON v.id  = cv1.vote_id
                JOIN   documents d ON d.id = v.document_id
                WHERE  EXTRACT(YEAR FROM d.date) BETWEEN %s AND %s
                  AND  d.date IS NOT NULL
                  AND  EXTRACT(YEAR FROM d.date) > 1900
                  AND  cv1.vote_position IN ('yes', 'no', 'abstain')
                  AND  cv2.vote_position IN ('yes', 'no', 'abstain')
                GROUP  BY cv1.country_id, cv2.country_id
                HAVING COUNT(*) >= %s
            """, [win_start, win_end, min_shared])
            pairs = cur.fetchall()

        # Build adjacency list from pairs above threshold
        adj = {}
        for a, b, agree, _shared in pairs:
            if agree >= threshold:
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)

        # All countries present in any pair (even below threshold)
        all_countries = set()
        for a, b, *_ in pairs:
            all_countries.add(a)
            all_countries.add(b)

        # Union-find connected components
        parent = {c: c for c in all_countries}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        for node, neighbours in adj.items():
            for nb in neighbours:
                union(node, nb)

        # Group by root, sort by descending size, assign bloc_index
        groups = {}
        for c in all_countries:
            groups.setdefault(find(c), []).append(c)
        blocs = sorted(groups.values(), key=len, reverse=True)

        rows = []
        for idx, members in enumerate(blocs):
            for country_id in members:
                rows.append((country_id, year, idx, win_start, win_end))

        with connection.cursor() as cur:
            cur.execute("DELETE FROM voting_blocs WHERE year = %s", [year])
            if rows:
                cur.executemany(
                    "INSERT INTO voting_blocs "
                    "(country_id, year, bloc_index, window_start, window_end) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    rows,
                )

        n_blocs = len(blocs)
        n_countries = len(all_countries)
        self.stdout.write(
            f'  {year}: {n_countries} countries → {n_blocs} blocs '
            f'(sizes: {", ".join(str(len(b)) for b in blocs[:6])}{"…" if n_blocs > 6 else ""})'
        )
