import logging.handlers
import yaml
from aiohttp import web

from file_streamer.signals import init_metrics_server, create_private_api_files_service, create_private_bucket, \
    init_session, destroy_session
from file_streamer.streamer.views.private_files import get_api_private_file

log = logging.getLogger(__name__)


async def healthcheck(request):
    return web.Response(status=200)


def deep_replace(target: dict, source: dict):
    for key in source:
        if key not in target:
            continue
        if isinstance(source[key], dict) and isinstance(target[key], dict):
            deep_replace(target[key], source[key])
        else:
            target[key] = source[key]


def get_config(config_path, secrets_path=None):
    with open(config_path, 'rt', encoding='UTF-8') as config_file:
        config = yaml.safe_load(config_file)
        if secrets_path:
            with open(secrets_path, 'rt', encoding='UTF-8') as secrets_file:
                secrets = yaml.safe_load(secrets_file)
                deep_replace(config, secrets)
        return config


async def create_app(args):
    config = get_config(args.config, args.secrets)
    app = web.Application()
    app['config'] = config
    app['args'] = args

    app.on_startup.extend((
        init_session,
        init_metrics_server,
        create_private_api_files_service,
        create_private_bucket
    ))

    app.on_cleanup.extend((
        destroy_session,
    ))

    app.router.add_route(
        'GET', '/health', healthcheck
    )
    app.router.add_route(
        'GET', '/api/file/private/{file_path}', get_api_private_file
    )
    return app
