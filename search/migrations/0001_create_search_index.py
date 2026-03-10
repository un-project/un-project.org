from django.db import migrations


CREATE_MATERIALIZED_VIEW = """
CREATE MATERIALIZED VIEW IF NOT EXISTS speech_search_index AS
SELECT
    s.id            AS speech_id,
    s.document_id,
    d.symbol,
    d.date,
    d.body,
    d.session,
    s.speaker_id,
    sp.name         AS speaker_name,
    sp.country_id,
    c.name          AS country_name,
    s.text,
    to_tsvector('english', s.text) AS search_vector
FROM speeches s
JOIN documents d ON d.id = s.document_id
JOIN speakers sp ON sp.id = s.speaker_id
LEFT JOIN countries c ON c.id = sp.country_id;
"""

CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_speech_search_vector
    ON speech_search_index USING GIN(search_vector);
"""

CREATE_UNIQUE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_speech_search_pk
    ON speech_search_index (speech_id);
"""

DROP_MATERIALIZED_VIEW = "DROP MATERIALIZED VIEW IF EXISTS speech_search_index;"


class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.RunSQL(CREATE_MATERIALIZED_VIEW, reverse_sql=DROP_MATERIALIZED_VIEW),
        migrations.RunSQL(CREATE_INDEX, reverse_sql="DROP INDEX IF EXISTS idx_speech_search_vector;"),
        migrations.RunSQL(CREATE_UNIQUE_INDEX, reverse_sql="DROP INDEX IF EXISTS idx_speech_search_pk;"),
    ]
