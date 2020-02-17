from contextlib import asynccontextmanager
import logging
from dataclasses import dataclass
from typing import Dict
from urllib.parse import urljoin

import asyncio
import aiobotocore
import aiohttp
from botocore.client import Config


log = logging.getLogger(__name__)


class ApiHttpException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


class InvalidResponseException(Exception):
    pass


@dataclass
class ApiResponse(object):
    file_key: str
    original_name: str


class PrivateBucketStorage(object):
    def __init__(self, s3_config, connect_timeout=60, read_timeout=60, retries=1):
        loop = asyncio.get_event_loop()
        self._config = s3_config
        self._session = aiobotocore.get_session(loop=loop)
        self._connection_config = Config(
            signature_version='s3',
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries={"max_attempts": retries}
        )

    @asynccontextmanager
    async def _client(self):
        async with self._session.create_client(
            's3',
            endpoint_url=f"http://{self._config['host']}",
            use_ssl=self._config['secure'],
            aws_secret_access_key=self._config['secret_access_key'],
            aws_access_key_id=self._config['access_key_id'],
            config=self._connection_config
        ) as client:
            yield client

    @asynccontextmanager
    async def get_bucket_key_response(self, file_key: str):
        async with self._client() as client:
            response = await client.get_object(Bucket=self._config['file_bucket'], Key=file_key)
            yield response


class ApiService(object):
    def __init__(
            self,
            api_connection: str,
            api_host: str,
            session: aiohttp.ClientSession,
    ):
        self._api_connection = api_connection
        self._api_host = api_host
        self._session = session

    async def get_file_key(self, request, file_path) -> ApiResponse:
        resp = await self._call_api(
            uri=urljoin(request.path, file_path),
            headers=request.headers
        )
        try:
            file_key = resp['file_name']
            original_name = resp['original_name']
        except KeyError as e:
            raise InvalidResponseException(resp) from e
        return ApiResponse(file_key=file_key, original_name=original_name)

    async def _call_api(self, uri: str, headers=None) -> Dict:
        url = urljoin(self._api_connection, uri)
        base_headers = {
            'Content-Type': 'application/json',
            "HOST": self._api_host,
        }
        if headers:
            base_headers.update(headers)
        async with self._session.get(url, headers=base_headers, allow_redirects=False) as resp:
            if resp.status != 200:
                raise ApiHttpException(status_code=resp.status)
            try:
                data = await resp.json()
                return data
            except Exception as e:
                raw = await resp.text()
                raise InvalidResponseException(raw) from e
