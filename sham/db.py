import asyncpg
from typing import Optional

SCHEMA_UPDATES = [
    # Version 0 is a no-op
    "SELECT 1",
    """
    CREATE TABLE asset (
        id SERIAL PRIMARY KEY NOT NULL,
        name TEXT NOT NULL,
        deleted BOOL NOT NULL
    );
    """,
    """
    CREATE TABLE tag (
        id SERIAL PRIMARY KEY NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        linked_asset_id INTEGER REFERENCES asset(id),
        UNIQUE (key, value)
    );
    """,
    """
    CREATE TABLE associated_tag (
        implied_by INTEGER NOT NULL REFERENCES tag(id),
        implies INTEGER NOT NULL REFERENCES tag(id) CHECK (implied_by <> implies),
        PRIMARY KEY (implied_by, implies)
    );
    """,
    """
    CREATE TABLE asset_tag (
        asset_id INTEGER NOT NULL REFERENCES asset(id),
        tag_id INTEGER NOT NULL REFERENCES tag(id),
        PRIMARY KEY (asset_id, tag_id)
    );
    """,
    """
    ALTER TABLE tag DROP CONSTRAINT tag_key_value_key;
    ALTER TABLE tag ADD UNIQUE (key, value, linked_asset_id);
    """,
]


async def _version_table_exists(conn) -> Optional[int]:
    return await conn.fetchval(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = '_sham_version'
        );
        """
    )


async def _create_version_table(conn):
    async with conn.transaction():
        await conn.execute(
            """
            CREATE TABLE _sham_version (
                version int PRIMARY KEY
            );
            """
        )
        await _update_schema_version(conn, 0)


async def fetch_schema_version(conn):
    row = await conn.fetchrow(
        """
        SELECT MAX(version) FROM _sham_version
        """
    )
    return row[0]


async def _update_schema_version(conn, version_number):
    await conn.execute(
        """
        INSERT INTO _sham_version VALUES ($1)
        """,
        version_number,
    )


async def _migrate_if_needed(conn):
    if not await _version_table_exists(conn):
        await _create_version_table(conn)
        assert await _version_table_exists(conn)

    schema_version = await fetch_schema_version(conn)

    updates_to_run = list(enumerate(SCHEMA_UPDATES))[schema_version + 1 :]
    for update_version, query in updates_to_run:
        async with conn.transaction():
            await conn.execute(query)
            await _update_schema_version(conn, update_version)

    assert await fetch_schema_version(conn) == len(SCHEMA_UPDATES) - 1


async def connect_to_db(username, password, ip="localhost", dbname="sham", port=5432):
    return await connect_to_db_by_url(
        f"postgresql://{username}:{password}@{ip}:{port}/{dbname}"
    )


async def connect_to_db_by_url(url):
    conn = await asyncpg.connect(url)
    await _migrate_if_needed(conn)

    return conn
