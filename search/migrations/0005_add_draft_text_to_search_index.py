from django.db import migrations


# Recreate search_index to include resolutions.draft_text:
#   - content column: title + full_text + draft_text (for headline snippets)
#   - search_vector:  draft_text at weight 'D' (same as full_text)
#   - WHERE filter:   also include rows where only draft_text is present
#     (covers vetoed/rejected SC draft stubs with no title or full_text)

DROP_VIEW = "DROP MATERIALIZED VIEW IF EXISTS search_index CASCADE;"

CREATE_VIEW = """
CREATE MATERIALIZED VIEW search_index AS
SELECT
    row_number() OVER ()::bigint  AS id,
    base.*
FROM (

    -- ── Speeches ──────────────────────────────────────────────────────────
    SELECT
        'speech'::text              AS item_type,
        s.id                        AS item_id,
        s.document_id               AS document_id,
        d.symbol                    AS document_symbol,
        d.date                      AS date,
        d.body                      AS body,
        d.session                   AS session,
        s.speaker_id                AS speaker_id,
        sp.name                     AS speaker_name,
        sp.country_id               AS country_id,
        c.name                      AS country_name,
        c.iso3                      AS country_iso3,
        s.text                      AS content,
        (
            setweight(to_tsvector('english', coalesce(sp.name,  '')), 'A') ||
            setweight(to_tsvector('english', coalesce(c.name,   '')), 'B') ||
            setweight(to_tsvector('english', coalesce(s.text,   '')), 'C')
        )                           AS search_vector
    FROM speeches s
    JOIN  documents d  ON d.id  = s.document_id
    JOIN  speakers  sp ON sp.id = s.speaker_id
    LEFT JOIN countries c ON c.id = sp.country_id

    UNION ALL

    -- ── Resolutions ────────────────────────────────────────────────────────
    SELECT
        'resolution'::text          AS item_type,
        r.id                        AS item_id,
        NULL::integer               AS document_id,
        coalesce(r.adopted_symbol, r.draft_symbol) AS document_symbol,
        NULL::date                  AS date,
        r.body                      AS body,
        r.session                   AS session,
        NULL::integer               AS speaker_id,
        NULL::text                  AS speaker_name,
        NULL::integer               AS country_id,
        NULL::text                  AS country_name,
        NULL::text                  AS country_iso3,
        coalesce(r.title, '')
            || ' ' || coalesce(r.full_text,  '')
            || ' ' || coalesce(r.draft_text, '') AS content,
        (
            setweight(to_tsvector('english', coalesce(r.adopted_symbol, r.draft_symbol, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(r.title,      '')), 'B') ||
            setweight(to_tsvector('english', coalesce(r.category,   '')), 'C') ||
            setweight(to_tsvector('english', coalesce(r.full_text,  '')), 'D') ||
            setweight(to_tsvector('english', coalesce(r.draft_text, '')), 'D')
        )                           AS search_vector
    FROM resolutions r
    WHERE coalesce(r.title, '') <> ''
       OR r.full_text  IS NOT NULL
       OR r.draft_text IS NOT NULL

) base;
"""

IDX_PK   = "CREATE UNIQUE INDEX idx_search_index_id     ON search_index (id);"
IDX_GIN  = "CREATE INDEX idx_search_index_vector  ON search_index USING GIN(search_vector);"
IDX_TYPE = "CREATE INDEX idx_search_index_type    ON search_index (item_type, item_id);"
IDX_BODY = "CREATE INDEX idx_search_index_body    ON search_index (body)       WHERE body       IS NOT NULL;"
IDX_CTRY = "CREATE INDEX idx_search_index_country ON search_index (country_id) WHERE country_id IS NOT NULL;"
IDX_SPKR = "CREATE INDEX idx_search_index_speaker ON search_index (speaker_id) WHERE speaker_id IS NOT NULL;"


class Migration(migrations.Migration):
    dependencies = [
        ('search', '0004_add_resolution_fulltext'),
    ]
    operations = [
        migrations.RunSQL(DROP_VIEW,    reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(CREATE_VIEW,  reverse_sql=DROP_VIEW),
        migrations.RunSQL(IDX_PK,   reverse_sql="DROP INDEX IF EXISTS idx_search_index_id;"),
        migrations.RunSQL(IDX_GIN,  reverse_sql="DROP INDEX IF EXISTS idx_search_index_vector;"),
        migrations.RunSQL(IDX_TYPE, reverse_sql="DROP INDEX IF EXISTS idx_search_index_type;"),
        migrations.RunSQL(IDX_BODY, reverse_sql="DROP INDEX IF EXISTS idx_search_index_body;"),
        migrations.RunSQL(IDX_CTRY, reverse_sql="DROP INDEX IF EXISTS idx_search_index_country;"),
        migrations.RunSQL(IDX_SPKR, reverse_sql="DROP INDEX IF EXISTS idx_search_index_speaker;"),
    ]
