import shutil
import string
from typing import Union, List
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4 as uuid

import aiofiles
import aiofiles.os


@dataclass
class TagInfo:
    pass


@dataclass
class SearchParams:
    pass


def asset_path_from_dir_and_id(asset_dir, asset_id):
    return Path(asset_dir) / str(asset_id)


# TODO: istm this would be better/faster to do in something like this in nginx
# It's not clear how permissions would work in that case though...
async def get_asset(asset_dir, asset_id) -> bytes:
    """
    - GET binary data for given asset_id
        - `GET /asset/<asset-id>`
    404 if asset not in DB / deleted in DB
    5XX if asset is in DB, but on in the filesystem
    """
    file_path = asset_path_from_dir_and_id(asset_dir, asset_id)

    # TODO: 404 on file not found
    async with aiofiles.open(file_path, "r+b") as f:
        return await f.read()


async def get_asset_tags(asset_id):
    """
    - GET tags for asset_id (all tags, including implied tags and assets the link to this one)
        - `GET /asset/<asset-id>/tags`
    """


# TODO: determine what should actually be returned
async def get_assets(conn, search_params: SearchParams) -> List[int]:
    """
    - GET paginated assets matching $SEARCH, returns:
        - `GET /assets?tag=<tag-id>&...`
        - asset_id
        - id to search from for next search
        - tags...? (this seems like it could get expensive, maybe only direct tags?)
    """

    # TODO: actually do a search, rather than returning everything
    return await conn.fetch("SELECT id FROM asset WHERE deleted = false;")


# TODO: is there a way to do file streaming?
# TODO: return type
async def post_asset(
    conn, asset_dir: Union[str, Path], unsanitized_file_name: str, file_contents: bytes
) -> int:
    """
    - POST new binary data and return asset_id
        - `POST /asset`
        - optionally include preview?
        - how does the client generate this?
    """
    # TODO: internationalization
    acceptable_characters = set(string.ascii_letters) | {" ", "_"} | set(string.digits)
    sanitized_file_name = "".join(
        c if c in acceptable_characters else "_" for c in unsanitized_file_name
    )

    # Write this to a temporary location on the same disk as the asset_dir.
    # If files somehow get left here we know we can delete them if they're old.
    # TODO: would tempfile.NamedTemporaryFile work here? is it fine to create
    # the temporary file then move it?
    # TODO: Should have a monitor for this (and admin disk space monitor)

    try:
        tmp_path = Path(asset_dir) / "tmp"
        # We get scary-looking logs if we don't look before we leap
        if not tmp_path.exists():
            await aiofiles.os.mkdir(tmp_path)
            print("Created path")
    except FileExistsError:
        # This will exist once the very first asset is uploaded, so we'll be
        # catching this exception a lot
        pass

    temp_file_path = Path(asset_dir) / "tmp" / str(uuid())
    async with aiofiles.open(temp_file_path, "w+b") as f:
        await f.write(file_contents)

    # Create an entry for a _deleted_ asset. This way, nothing assumes that this
    # asset exists.
    asset_id = await conn.fetchval(
        "INSERT INTO asset (name, deleted) VALUES ($1, $2) RETURNING id",
        sanitized_file_name,
        True,
    )

    # Move the asset into its final place
    destination_file_path = asset_path_from_dir_and_id(asset_dir, asset_id)
    await aiofiles.os.rename(temp_file_path, destination_file_path)

    # "un"-delete the asset, other things can now access it
    await conn.execute("UPDATE asset SET deleted = $1", False)

    return asset_id

    # Hey! No transactions (I thought I'd need one at first)


async def post_tag(tag: TagInfo):
    """
    - POST new tag and return... tag_id? (will the frontend use tag ids..?)
        - `POST /tag`
    """


async def delete_asset(asset_id):
    """
    - DELETE asset_id
        - `DELETE /asset/<asset-id>`
    """


async def post_tag_on_asset(asset_id, tag_id):
    """
    - Associate tag with asset (should the client have to create the tag, or should this be an upsert?)
        - `POST /asset/<asset-id>/tag`
        - Should this be a put?
    """


async def delete_tag_from_asset(asset_id, tag_id):
    """
    - Tags are never deleted, associations are just removed
        - `DELETE /asset/<asset-id>/tag/<tag-id>`
    """
