import argparse
import logging


import asyncio
import uvloop
from aiohttp import web

from file_streamer.streamer.app import create_app


log = logging.getLogger(__name__)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=2000)
    ap.add_argument("--host", default='0.0.0.0')
    ap.add_argument("--api_connection", default='http://api:4998')
    ap.add_argument("--api_host", default='api.com:5000')
    ap.add_argument("--config", default='/file_streamer/config/.../app.yaml')
    ap.add_argument("--secrets", default=None)
    ap.add_argument("--debug", default=False)
    return ap.parse_args()


def main():
    args = parse_args()
    host = args.host
    port = args.port
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    log.info(f"Listening {host}:{port}")
    web.run_app(create_app(args), host=host, port=port)


if __name__ == '__main__':
    main()
