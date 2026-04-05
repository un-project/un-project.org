import os
import re

import pytest
from django.db import connection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_FILE = os.path.join(BASE_DIR, 'docker', 'init', '01_schema.sql')

# Extra DDL for tables/columns added after the schema dump.
# Uses schema-qualified names because the schema SQL sets search_path = ''.
_EXTRA_SQL = """
SET search_path TO public;

ALTER TABLE public.speakers ADD COLUMN IF NOT EXISTS organization VARCHAR(400);

CREATE TABLE IF NOT EXISTS public.search_index (
    id          bigserial PRIMARY KEY,
    item_type   varchar(20),
    item_id     integer,
    document_id integer,
    document_symbol varchar(50),
    date        date,
    body        varchar(2),
    session     integer,
    speaker_id  integer,
    speaker_name varchar(300),
    country_id  integer,
    country_name varchar(300),
    country_iso3 varchar(3),
    content     text,
    search_vector tsvector
);

ALTER TABLE public.resolutions
    ADD COLUMN IF NOT EXISTS full_text TEXT,
    ADD COLUMN IF NOT EXISTS crunsc_id VARCHAR(30);

ALTER TABLE public.documents
    ADD COLUMN IF NOT EXISTS is_general_debate BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS public.resolution_citations (
    id          SERIAL PRIMARY KEY,
    citing_id   INTEGER NOT NULL REFERENCES public.resolutions(id) ON DELETE CASCADE,
    cited_symbol TEXT NOT NULL,
    cited_id    INTEGER REFERENCES public.resolutions(id) ON DELETE SET NULL,
    weight      INTEGER NOT NULL DEFAULT 1,
    UNIQUE (citing_id, cited_symbol)
);

CREATE TABLE IF NOT EXISTS public.general_debate_entries (
    id          SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES public.documents(id) ON DELETE SET NULL,
    country_id  INTEGER REFERENCES public.countries(id) ON DELETE SET NULL,
    speaker_id  INTEGER REFERENCES public.speakers(id) ON DELETE SET NULL,
    speaker_name TEXT NOT NULL,
    salutation  VARCHAR(20),
    ga_session  INTEGER NOT NULL,
    meeting_date DATE,
    undl_id     VARCHAR(30),
    undl_link   TEXT
);

CREATE TABLE IF NOT EXISTS public.country_ideal_points (
    id          SERIAL PRIMARY KEY,
    country_id  INTEGER REFERENCES public.countries(id) ON DELETE CASCADE,
    iso3        VARCHAR(3) NOT NULL,
    year        INTEGER NOT NULL,
    ideal_point DOUBLE PRECISION NOT NULL,
    se          DOUBLE PRECISION,
    UNIQUE (iso3, year)
);

CREATE TABLE IF NOT EXISTS public.speech_search_index (
    speech_id   integer PRIMARY KEY,
    document_id integer,
    symbol      varchar(30),
    date        date,
    body        varchar(2),
    session     integer,
    speaker_id  integer,
    speaker_name varchar(300),
    country_id  integer,
    country_name varchar(300),
    text        text,
    search_vector text
);
"""


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Load the application schema (all unmanaged models) into the test DB."""
    with django_db_blocker.unblock():
        with open(SCHEMA_FILE) as f:
            raw = f.read()

        # Strip psql meta-commands (\restrict, \unrestrict, etc.)
        sql = re.sub(r'^\\[^\n]*$', '', raw, flags=re.MULTILINE)

        with connection.cursor() as cursor:
            cursor.execute(sql)

        # Reset search_path (the schema dump sets it to '' for the session)
        # then apply post-dump additions.
        with connection.cursor() as cursor:
            cursor.execute(_EXTRA_SQL)
