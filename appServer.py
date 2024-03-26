import aiohttp
from aiohttp import web
import asyncio
import socket
import pickle
import struct
# TODO at now larger files will load first then make pickle so yielding not works i mean it is not asynchronously so send status, headers then body in binary
# TODO Message size 9136275 exceeds limit 4194304
CHUNK_SIZE = 1024*1024 # 1 MB or 1 forth of limit size
PAYLOAD_SIZE = struct.calcsize("Q") # header size which contains size of message
class Server:
    def __init__(self):
        self.ws = None
        # TODO sometimes Queue will leak behind for example in case of downloading or heavy loading
        self.received_data = asyncio.Queue()
        self.ClientNo = 0 # NOW we only support one client at a time
    async def handle_client(self, request):
        self.ws = web.WebSocketResponse()
        if self.ClientNo >= 1: return self.ws
        self.received_data = asyncio.Queue()
        print('connection established')
        self.ClientNo+=1
        await self.ws.prepare(request)
        
        async for msg in self.ws:
            await self.received_data.put(msg.data)
            
        print("Client disconnected")
        self.ClientNo-=1
        return self.ws
    
    async def forward_request(self, request):
        if self.ClientNo == 0: return web.Response(text="Server is running please connect a client first")
        url = request.path
        data = await request.read()
        async with aiohttp.ClientSession() as session:
            # send this to client session
            await self.send({
                'method': request.method,
                'url': url,
                'headers': dict(request.headers),
                'data': data
            })
            data = await self.recv()
            return web.Response(body=data['body'], status=data['status'], headers=data['headers'])

    async def recv(self):
        # RECV message
        data = await self.received_data.get()
        packed_msg_size = struct.unpack("Q",data[:PAYLOAD_SIZE])[0]
        while len(data) < packed_msg_size:
            data += await self.received_data.get()
        data = data[PAYLOAD_SIZE:]
        return pickle.loads(data)
    
    async def send(self, data):
        # SEND message
        response_bytes = pickle.dumps(data)
        response_size = len(response_bytes)
        message = struct.pack("Q",response_size)+response_bytes
        # Send the response data in chunks
        for offset in range(0, len(message), CHUNK_SIZE):
            chunk = message[offset:offset + CHUNK_SIZE]
            await self.ws.send_bytes(chunk)

server = Server()


async def main(*args, **kwrgs):
    app = web.Application()
    app.router.add_route('GET', '/api_portforwardpy/{path:.*}', server.handle_client)
    app.router.add_route('*', '/{path:.*}', server.forward_request)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Forward server started on port 8080")
    return app
# cd /mnt/c/ThefCraft/thefcraft/projectWeb/flaskPortForwarder
# gunicorn appServer:main -w 1 -k aiohttp.worker.GunicornWebWorker -b 0.0.0.0:8001
if __name__ == '__main__':
    for host in [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]:
        print(f'Starting server on http://{host}:8080')
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    loop.run_forever()
