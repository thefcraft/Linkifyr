import aiohttp
from aiohttp import web
import asyncio
import socket
import json
import base64

class Server:
    def __init__(self):
        self.ws = None
        self.received_data = asyncio.Queue()
    async def handle_client(self, request):
        self.ws = web.WebSocketResponse()
        print('connection established')
        await self.ws.prepare(request)
        
        async for msg in self.ws:
            data = json.loads(msg.data)
            await self.received_data.put(data)
            
        print("Client disconnected")
        return self.ws
    
    async def forward_request(self, request):
        url = request.path
        headers = {header: value for header, value in request.headers.items()}
        data = await request.read()

        async with aiohttp.ClientSession() as session:
            # send this to client session
            data_base64 = base64.b64encode(data).decode()
            await self.send(json.dumps({
                'method': request.method,
                'url': url,
                'headers': headers,
                'data': data_base64
            }))
            data = await self.receive_data()
            return web.Response(body=base64.b64decode(data['body']), status=data['status'], headers=data['headers'])

    async def receive_data(self):
        return await self.received_data.get()
    
    async def send(self, data):
        await self.ws.send_str(data)

server = Server()


async def main(*args, **kwrgs):
    app = web.Application()
    app.router.add_route('GET', '/api/{path:.*}', server.handle_client)
    app.router.add_route('*', '/{path:.*}', server.forward_request)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8082)
    await site.start()
    print("Forward server started on port 8082")
    return app

# gunicorn appServer:main -w 1 -k aiohttp.worker.GunicornWebWorker -b 0.0.0.0:8001
if __name__ == '__main__':
    for host in [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]:
        print(f'Starting server on http://{host}:8080')
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    loop.run_forever()