import logging.handlers

from aiohttp import web, ClientSession, ClientTimeout, DummyCookieJar

from file_streamer.streamer.services.api import PrivateBucketStorage, ApiService

log = logging.getLogger(__name__)


async def create_private_api_files_service(app: web.Application) -> None:
    args = app['args']
    private_api_file_service = ApiService(
        api_connection=args.api_connection,
        api_host=args.api_host,
        session=app['session']
    )
    app['api_service'] = private_api_file_service


async def create_private_bucket(app: web.Application) -> None:
    app_config = app['config']
    config = app_config['files']['riak_s3_private']
    config['secret_access_key'] = app_config['files']['riak_s3']['secret_access_key']
    private_bucket = PrivateBucketStorage(
        s3_config=config,
        connect_timeout=5,
        read_timeout=60,
        retries=3
    )
    app['private_bucket'] = private_bucket


async def init_session(app: web.Application) -> None:
    app['session'] = ClientSession(
        timeout=ClientTimeout(5),
        cookie_jar=DummyCookieJar(),
    )


async def destroy_session(app: web.Application) -> None:
    session: ClientSession = app['session']
    if not session.closed:
        await session.close()
