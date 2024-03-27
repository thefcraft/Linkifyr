import websockets
import aiohttp
from aiohttp import web, ClientSession
import requests
import asyncio
import pickle
import struct

# Constants
CHUNK_SIZE = 1024 * 1024 * 4  # 4 MB
PAYLOAD_SIZE = struct.calcsize("Q")  # Header size which contains size of message

PORT = 80
URL = f'http://127.0.0.1:{PORT}/'
SERVER_URL = 'portforwardpy.onrender.com' #'localhost:8080'

async def client_connect(url, localhost=False):
    print('trying to connect to server...')
    async with ClientSession() as session:
        conn = websockets.connect if localhost else session.ws_connect
        async with conn(url) as ws:
            print('connection established')
            print(f'YOUR SITE {URL} is live at https://{SERVER_URL}')
            send = ws.send if localhost else ws.send_bytes
            recv = ws.recv if localhost else ws.receive_bytes
            while True: 
                # RECV message
                data = await recv()

                packed_msg_size = struct.unpack("Q",data[:PAYLOAD_SIZE])[0]
                data = data[PAYLOAD_SIZE:]
                while len(data) < packed_msg_size:
                    data += await recv()
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
                        await send(chunk)


async def main():
    url = f"ws://{SERVER_URL}/api_portforwardpy/"
    if SERVER_URL.startswith('localhost'):
        await client_connect(url)
    else:
        task = asyncio.create_task(client_connect(url))
        await asyncio.gather(task)
    
if __name__ == '__main__':
    asyncio.run(main())
