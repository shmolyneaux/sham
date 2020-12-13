import asyncio
import random
import requests
import subprocess
import tempfile
import time
from contextlib import contextmanager

import pytest
import urllib3

from sham import __version__, db, app

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

def is_server_up(url):
    try:
        return bool(requests.get(url + "/assets"))
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture
def db_url():
    url = subprocess.check_output(["pg_tmp"], text=True).strip()
    return url

@pytest.fixture
def sham_server_url(db_url):
    try:
        server_is_up = False
        for _startup_attempt in range(10):
            port = str(random.randint(10000, 20000))
            p = subprocess.Popen(["python3", "-m", "sham", "--db_url", db_url, "--port", port])
            sham_url = f"http://localhost:{port}"

            for _connection_attempt in range(200):
                server_is_up = is_server_up(sham_url)
                if server_is_up:
                    break

                # Sleep a small amount to give the server time to come up
                time.sleep(0.02)

                # If the process has a return code, it died. Try again.
                if p.poll():
                    break
            else:
                p.kill()

            if server_is_up:
                break
        else:
            raise AssertionError("Couldn't start server")
        yield sham_url
    finally:
        p.kill()


async def test_schema_version(db_url):
    assert __version__ == "0.1.0"

    conn = await db.connect_to_db_by_url(db_url)

    assert await db.fetch_schema_version(conn) == len(db.SCHEMA_UPDATES) - 1


async def test_get_assets(db_url):
    conn = await db.connect_to_db_by_url(db_url)

    with tempfile.TemporaryDirectory() as d:
        assert await app.get_assets(conn, None) == []
        assert (await app.post_asset(conn, d, "My file name", b"12345")) == 1

        asset_data = await app.get_asset(d, 1)
        assert asset_data == b"12345"

        assets = await app.get_assets(conn, None)
        assert [asset['id'] for asset in assets] == [1]

        assert (await app.post_asset(conn, d, "Another Asset", b"24601")) == 2
        assets = await app.get_assets(conn, None)
        assert [asset['id'] for asset in assets] == [1, 2]

        print("done")


def test_fullup(sham_server_url):
    url = sham_server_url

    # We start out with no assets
    res = requests.get(url + "/assets").json()
    assert res == {
        "asset": []
    }

    # We insert an asset and get its id
    files = {"file": ("my_file_name.foo", "some,data,to,send\n")}
    res = requests.post(url + "/asset", files=files).json()
    assert res == {"id": 1}

    # When we get the asset, we get back an octet-stream
    res = requests.get(url + "/asset/1")
    assert res
    assert res.content == b"some,data,to,send\n"
    assert res.headers.get('Content-Type') == 'application/octet-stream'

    # When we get the asset as a .txt, we get back text/plain
    res = requests.get(url + "/asset/1.txt")
    assert res
    assert res.content == b"some,data,to,send\n"
    assert res.headers.get('Content-Type') == 'text/plain'

    # And similarly with .png and image/png
    res = requests.get(url + "/asset/1.png")
    assert res
    assert res.content == b"some,data,to,send\n"
    assert res.headers.get('Content-Type') == 'image/png'

    # We see this single element when we get all assets
    res = requests.get(url + "/assets").json()
    assert res == {
        "asset": [{"id": 1}]
    }

    # Let's upload another file and see we got the next id
    files = {"file": ("my_file_name.foo", "more,data,to,send\n")}
    res = requests.post(url + "/asset", files=files).json()
    assert res == {"id": 2}

    # Now we should see both when we get the assets
    res = requests.get(url + "/assets").json()
    assert res == {
        "asset": [{"id": 1}, {"id": 2}]
    }
