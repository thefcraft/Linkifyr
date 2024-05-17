import aiohttp
import asyncio
import pickle
import struct
import requests
import sys

# Constants
CHUNK_SIZE = 1024 * 1024 * 4  # 4 MB
PAYLOAD_SIZE = struct.calcsize("Q")  # Header size which contains size of message

PORT = 5000
URL = f'http://127.0.0.1:{PORT}/'
SERVER_URL,SERVER_PROTOCOL = 'dev.thefcraft.site', 'https'
# SERVER_URL, SERVER_PROTOCOL = '127.0.0.1:80', 'http' # use custom dns for testing purposes

async def client_connect():
    print('trying to connect to server...')
    client_id = requests.get(f'{SERVER_PROTOCOL}://{SERVER_URL}/api_get_portforwardpy').json()['client_id']
    print("client_id : ", client_id)
    url = f"ws://{SERVER_URL}/api_portforwardpy/{client_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            print('connection established')
            print(f'YOUR SITE {URL} is live at {SERVER_PROTOCOL}://{client_id}.{SERVER_URL}')

            while True: 
                # RECV message
                data = await ws.receive_bytes()
                print(data)

                packed_msg_size = struct.unpack("Q", data[:PAYLOAD_SIZE])[0]
                data = data[PAYLOAD_SIZE:]
                while len(data) < packed_msg_size:
                    data += await ws.receive_bytes()
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
                    message = struct.pack("Q", response_size) + response_bytes
                    # Send the response data in chunks
                    for offset in range(0, len(message), CHUNK_SIZE):
                        chunk = message[offset:offset + CHUNK_SIZE]
                        await ws.send_bytes(chunk)


async def main():
    await client_connect()
    
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('quiting...')
        sys.exit(0)
