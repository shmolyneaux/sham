import argparse
import mimetypes
import string
from pathlib import Path

from sanic import response
from sanic import Sanic
from sanic.log import logger
from sanic.response import json

from . import app
from . import db

# NOTE: Nothing here is runnable yet

server = Sanic(name="sham")

config = {
    "asset_dir": Path("~/tmp").expanduser().as_posix(),
    "db_user": "stephen",
    "db_pass": "password",
}


async def get_db_conn():
    # TODO: connection pooling
    if db_url := config.get("db_url"):
        return await db.connect_to_db_by_url(db_url)

    return await db.connect_to_db(config["db_user"], config["db_pass"])


@server.route("/assets/<asset_id_with_extension>", methods=["GET"])
async def get_asset(request, asset_id_with_extension):
    # TODO: many we should allow {asset-id}.{whatever-extension}, and guess the
    # mime types? Otherwise everything will be octet streams...
    #
    # Or we could save/load the mime type in the DB?

    # TODO: error handling
    asset_id = int(Path(asset_id_with_extension).stem)

    return response.raw(
        # TODO: error handling
        await app.get_asset(config["asset_dir"], asset_id),
        headers={
            "Content-Type": mimetypes.guess_type(asset_id_with_extension)[0]
            or "application/octet-stream"
        },
    )


@server.route("/assets", methods=["GET"])
async def get_assets(request):
    conn = await get_db_conn()

    assets = await app.get_assets(conn, app.SearchParams)
    return json({"asset": [{"id": asset_id["id"]} for asset_id in assets]})


@server.route("/assets", methods=["POST"])
async def post_asset(request):
    upload_file = request.files.get("file")
    if not upload_file:
        # TODO: good error
        raise Exception("no upload file")

    if len(upload_file.body) > 50e6:
        # TODO: good error
        raise Exception("file body too large")

    conn = await get_db_conn()
    # TODO: is there a way to do file streaming?
    # https://sanic.readthedocs.io/en/latest/sanic/streaming.html
    asset_id = await app.post_asset(
        conn, config["asset_dir"], upload_file.name, upload_file.body
    )

    return json({"id": asset_id})


@server.route("/tags", methods=["POST"])
async def post_tag(request):
    # TODO: Use jsonschema here?

    key = request.json.get("key")
    value = request.json.get("value")
    linked_asset_id = request.json.get("linked_asset_id")

    assert isinstance(key, str)
    assert isinstance(value, str)
    assert isinstance(linked_asset_id, int) or linked_asset_id == None

    conn = await get_db_conn()
    tag_id = await app.post_tag(
        conn,
        app.TagInfo(
            key=request.json["key"],
            value=request.json["value"],
            linked_asset_id=request.json.get("linked_asset_id"),
        ),
    )

    return json({"id": tag_id})


@server.route("/assets/<asset_id>/tags", methods=["POST"])
async def post_tag_on_asset(request, asset_id):
    try:
        asset_id = int(asset_id)
    except ValueError:
        # TODO: Return 4xx error
        raise AssertionError(f"{asset_id} is not an int")

    # TODO: Use jsonschema here?

    tag_id = request.json.get("tag_id")
    assert isinstance(tag_id, int)

    conn = await get_db_conn()
    tag_id = await app.post_tag_on_asset(conn, asset_id=asset_id, tag_id=tag_id)

    return json({"result": "you did it!"})


@server.route("/assets/<asset_id>/tags", methods=["GET"])
async def get_tags_on_asset(request, asset_id):
    try:
        asset_id = int(asset_id)
    except ValueError:
        # TODO: Return 4xx error
        raise AssertionError(f"{asset_id} is not an int")

    conn = await get_db_conn()
    tag_ids = await app.get_asset_tags(conn, asset_id=asset_id,)

    return json(tag_ids)


@server.route("/assets/<asset_id>/tags/<tag_id>", methods=["DELETE"])
async def delete_tag_on_asset(request, asset_id, tag_id):
    try:
        asset_id = int(asset_id)
    except ValueError:
        # TODO: Return 4xx error
        raise AssertionError(f"{asset_id} is not an int")

    try:
        tag_id = int(tag_id)
    except ValueError:
        # TODO: Return 4xx error
        raise AssertionError(f"{tag_id} is not an int")

    conn = await get_db_conn()
    await app.delete_tag_from_asset(
        conn, asset_id=asset_id, tag_id=tag_id,
    )

    return json({"result": "you did it!"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset_dir")
    parser.add_argument("--db_url")
    parser.add_argument("--db_user")
    parser.add_argument("--db_pass")
    parser.add_argument("-p", "--port", default=8000)

    args = parser.parse_args()
    config["db_url"] = args.db_url
    config["db_user"] = config["db_user"] or args.db_user
    config["db_pass"] = config["db_pass"] or args.db_pass

    server.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
