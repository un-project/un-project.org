import os
import re

import pytest
from django.db import connection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_FILE = os.path.join(BASE_DIR, 'docker', 'init', '01_schema.sql')

# Extra DDL for tables/columns added after the schema dump
_EXTRA_SQL = """
ALTER TABLE speakers ADD COLUMN IF NOT EXISTS organization VARCHAR(400);

CREATE TABLE IF NOT EXISTS search_index (
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

CREATE TABLE IF NOT EXISTS speech_search_index (
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

        with connection.cursor() as cursor:
            cursor.execute(_EXTRA_SQL)
