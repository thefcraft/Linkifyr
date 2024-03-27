from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import JSONResponse
import asyncio
import pickle
import struct

#TODO slow speed for downloading of large files as it first send full file to server then start downloading

app = FastAPI()

# Constants
CHUNK_SIZE = 1024 * 1024 * 4 # 4 MB
PAYLOAD_SIZE = struct.calcsize("Q")  # Header size which contains size of message

class Server:
    def __init__(self):
        self.client_connected = []
        self.ws: list[WebSocket] = []
        self.received_data: list[asyncio.Queue] = []
        self.client_count = 0
    async def handle_client(self, websocket: WebSocket):
        await websocket.accept()
        
        server.ws.append(websocket)
        server.client_connected.append(True)
        self.received_data.append(asyncio.Queue())
        idx = self.client_count
        print("Client connected IDX: ", idx)
        self.client_count += 1
        try:
            while True:
                # RECV message
                data = await self.ws[idx].receive_bytes()
                packed_msg_size = struct.unpack("Q",data[:PAYLOAD_SIZE])[0]
                data = data[PAYLOAD_SIZE:]
                while len(data) < packed_msg_size:
                    data += await self.ws[idx].receive_bytes()
                await self.received_data[idx].put(data)
        except WebSocketDisconnect:
            self.client_connected = False
            self.ws = None
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            print('quit...')
            
    async def recv(self, idx):
        data = await self.received_data[idx].get()
        return pickle.loads(data)
    
    async def send(self, data, idx):
        # SEND message
        response_bytes = pickle.dumps(data)
        response_size = len(response_bytes)
        message = struct.pack("Q",response_size)+response_bytes
        # Send the response data in chunks
        for offset in range(0, len(message), CHUNK_SIZE):
            chunk = message[offset:offset + CHUNK_SIZE]
            await self.ws[idx].send_bytes(chunk)

server = Server()

# WebSocket endpoint
@app.websocket("/api_portforwardpy")
async def websocket_endpoint(websocket: WebSocket):
    await server.handle_client(websocket)
    
@app.get("/{url:path}")
@app.post("/{url:path}")
async def forward_request(url: str, request: Request):
    idx=0
    if not server.client_connected[idx]:
        return JSONResponse(content={"error": "No client connected"}, status_code=400)
    else:
        data = await request.body()
        await server.send({
            'method': request.method,
            'url': url,
            'headers': dict(request.headers),
            'data': data
        }, idx=idx)
        data = await server.recv(idx=idx)
        
        # Create a FastAPI Response object
        fastapi_response = Response(content=data['body'], status_code=data['status'])

        # Set headers in the FastAPI Response object
        for header, value in data['headers'].items():
            fastapi_response.headers[header] = value
            
        return fastapi_response
        

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
