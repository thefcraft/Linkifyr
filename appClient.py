import asyncio
import json
import base64
from aiohttp import web, ClientSession

URL = 'http://localhost:5000'
# URL = 'http://httpforever.com' ERROR: some errors in headers

async def client_connect(url):
    async with ClientSession() as session:
        async with session.ws_connect(url) as ws:
            print('connection established')
            # await ws.send_str('connection established') 
            async for msg in ws:
                data = json.loads(msg.data)
                async with session.request(data['method'], f"{URL}{data['url']}", headers=data['headers'], data=base64.b64decode(data['data'])) as response:
                    response_content = await response.read()
                    # Encode the response body to base64
                    response_body_base64 = base64.b64encode(response_content).decode()
                
                    # Create a dictionary with response data
                    response_data = {
                        'status': response.status,
                        'headers': dict(response.headers),
                        'body': response_body_base64
                    }
                    # Serialize the dictionary to JSON string
                    response_json = json.dumps(response_data)
                    # Send the JSON string over WebSocket
                    await ws.send_str(response_json)

async def main():
    url = "ws://localhost:8081/api/"
    task = asyncio.create_task(client_connect(url))
    await asyncio.gather(task)

if __name__ == "__main__":
    asyncio.run(main())