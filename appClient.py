import asyncio
import pickle
import aiohttp
from aiohttp import web

import struct
# TODO at now larger files will load first then make pickle so yielding not works i mean it is not asynchronously so send status, headers then body in binary
# TODO Message size 9136275 exceeds limit 4194304
CHUNK_SIZE = 1024*1024 # 1 MB or 1 forth of limit size
PAYLOAD_SIZE = struct.calcsize("Q") # header size which contains size of message

# TODO: flask redirect('files') not working fine 
# TODO: /files != /files/
# TODO: don't use http://localhost:5000 instead use http://127.0.0.1:5000
PORT = 5000
URL = f'http://127.0.0.1:{PORT}'

async def client_connect(url):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            print('connection established')
            is_payload_header = True
            async for msg in ws:
                # RECV message
                if is_payload_header:
                    is_payload_header = False
                    data = msg.data
                    packed_msg_size = struct.unpack("Q",data[:PAYLOAD_SIZE])[0]
                
                if len(data) < packed_msg_size:
                    data += msg.data
                else:
                    is_payload_header = True
                    data = data[PAYLOAD_SIZE:]
                    data = pickle.loads(data)
                
                    async with session.request(data['method'], f"{URL}{data['url']}", headers=data['headers'], data=data['data']) as response:
                        print(f"{data['method']}: {URL}{data['url']}")
                        response_content = await response.read()
                        # Create a dictionary with response data
                        response_data = {
                            'status': response.status,
                            'headers': dict(response.headers),
                            'body': response_content
                        }
                        # SEND message
                        response_bytes = pickle.dumps(response_data)
                        response_size = len(response_bytes)
                        message = struct.pack("Q",response_size)+response_bytes
                        # Send the response data in chunks
                        for offset in range(0, len(message), CHUNK_SIZE):
                            chunk = message[offset:offset + CHUNK_SIZE]
                            await ws.send_bytes(chunk)
                        # await ws.send_bytes(message)


async def main():
    url = "ws://localhost:8080/api_portforwardpy/"
    # url = "ws://portforwardpy.onrender.com/api/"
    task = asyncio.create_task(client_connect(url))
    await asyncio.gather(task)

if __name__ == '__main__':
    asyncio.run(main())
