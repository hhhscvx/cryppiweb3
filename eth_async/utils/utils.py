import json
import os

import aiohttp
from eth_async.exceptions import HTTPException


def join_path(path: str | tuple | list) -> str:
    if isinstance(path, str):
        return path
    return str(os.path.join(*path))  # ex. ('/', 'home', 'kirill')


def read_json(path: str | tuple | list, encoding: str | None = None) -> list | dict:
    path = join_path(path)
    return json.load(open(path, encoding=encoding))


async def async_get(url: str, headers: dict | None = None, **kwargs) -> dict | None:
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, **kwargs) as resp:
            if resp.status <= 201:
                return resp.json()

            raise HTTPException(response=resp, status_code=resp.status)
