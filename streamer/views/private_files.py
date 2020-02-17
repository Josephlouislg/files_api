import logging.handlers

from aiohttp import web

from file_streamer.streamer.services.api import ApiService, ApiHttpException, \
    PrivateBucketStorage, ApiResponse

log = logging.getLogger(__name__)


async def get_api_private_file(request):
    file_path = request.match_info.get('file_path', None)
    if not file_path:
        web.Response(status=404)

    api_service: ApiService = request.app['api_service']
    private_bucket: PrivateBucketStorage = request.app['private_bucket']

    try:
        api_resp: ApiResponse = await api_service.get_file_key(request, file_path)
    except ApiHttpException as http_exceptions:
        return web.Response(status=http_exceptions.status_code)

    async with private_bucket.get_bucket_key_response(api_resp.file_key) as bucket_object:
        headers = {"Content-Disposition": f"attachment;filename={api_resp.original_name}"}
        response = web.StreamResponse(status=200, headers=headers)

        response.enable_compression()
        response.content_size = bucket_object['ResponseMetadata']['HTTPHeaders']['content-length']
        await response.prepare(request)
        async with bucket_object['Body'] as stream:
            async for chunk, *_ in stream.iter_chunks():
                await response.write(chunk)
            await response.write_eof()
            return response
