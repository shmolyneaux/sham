# Sham

Sham is an asset management server built with Python, [Sanic](https://sanic.dev/), and PostgreSQL. It provides a REST API for uploading, retrieving, tagging, and deleting binary assets (files), with a tagging system that supports key-value tags and tag-to-asset linking. Sham uses automatic database schema migrations and includes experimental use of Python 3.10 pattern matching.

## Building and Testing

**Prerequisites:** Python 3.10+, [Poetry](https://python-poetry.org/), and [`pg_tmp`](https://eradman.com/ephemeralpg/) (for tests).

Install dependencies:
```
poetry install
```

Run tests:
```
make test
```

Run the server in development:
```
poetry run sham --db_url <postgresql-url>
```

## Usage

Sham exposes a REST API. Here are some example interactions using `curl`:

```bash
# Upload an asset
curl -F "file=@photo.png" http://localhost:8000/assets
# => {"id": 1}

# Retrieve the asset (with MIME type inferred from extension)
curl http://localhost:8000/assets/1.png -o photo.png

# List all assets
curl http://localhost:8000/assets

# Create a tag
curl -X POST http://localhost:8000/tags \
  -H "Content-Type: application/json" \
  -d '{"key": "category", "value": "nature", "linked_asset_id": null}'
# => {"id": 1}

# Apply a tag to an asset
curl -X POST http://localhost:8000/assets/1/tags \
  -H "Content-Type: application/json" \
  -d '{"tag_id": 1}'

# Delete an asset (soft-delete)
curl -X DELETE http://localhost:8000/assets/1
```

## Features

- Upload and retrieve binary assets via REST API
- Automatic MIME type detection based on file extension
- Key-value tagging system with support for tags linked to other assets
- Associate and remove tags on assets
- Automatic PostgreSQL schema migrations on startup
- CORS support for cross-origin requests
- Soft-delete for assets (assets are marked as deleted, not removed from disk)

## Limitations

- No authentication or authorization
- No connection pooling for database connections
- File uploads are buffered in memory (no streaming support), with a 50 MB limit
- No pagination for asset or tag listing
- Search/filtering of assets by tags is not yet implemented
- Error handling is minimal in several endpoints
- The file name sanitization only supports ASCII characters

## Running on WSL

To start PostgreSQL:
```
sudo service postgresql start
```

## Python 3.10 Pattern Matching

This project uses Python 3.10 pattern matching (in `sham/error.py`). The original development used a pre-release branch of Python 3.10 with custom-built dependencies:

- Pattern Matching Python Version: `d5f32da322`
- uvloop version: `c808a663b2` (version "0.16.0.dev0" hardcoded in setup.py)
- asyncpg version: `a308a9736e`

## History

Development on Sham started on 2021-11-13, and largely stopped on 2021-11-14:

- 2021-11-13 — Initial commit with the full application: Sanic-based REST API for asset uploads/downloads, key-value tagging system, PostgreSQL schema migrations, pattern-matching-based error utilities, integration tests, and CORS support
- 2021-11-14 — Fixed database connection leaks by converting `get_db_conn` to an async context manager that properly closes connections
