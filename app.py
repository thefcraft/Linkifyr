from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import JSONResponse
import asyncio
import pickle
import struct
import uuid
from urllib.parse import urlparse
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib
import secrets

#TODO slow speed for downloading of large files as it first send full file to server then start downloading

app = FastAPI()

# Constants
CHUNK_SIZE = 1024 * 1024 * 4 # 4 MB
PAYLOAD_SIZE = struct.calcsize("Q")  # Header size which contains size of message
DOMAIN_DEPTH = 3 # *.dev.thefcraft.site => 3 and *.example.com => 2

class Server:
    def __init__(self):
        self.clients = {}
        
    async def handle_client(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        
        self.clients[client_id] = {
            "ws": websocket,
            "received_data": asyncio.Queue()
        }
        
        try:
            while True:
                # RECV message
                data = await websocket.receive_bytes()
                packed_msg_size = struct.unpack("Q", data[:PAYLOAD_SIZE])[0]
                data = data[PAYLOAD_SIZE:]
                while len(data) < packed_msg_size:
                    data += await websocket.receive_bytes()
                await self.clients[client_id]["received_data"].put(data)
        except WebSocketDisconnect:
            del self.clients[client_id]
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            print(f'Client {client_id} disconnected.')
            
    async def recv(self, client_id: str):
        data = await self.clients[client_id]["received_data"].get()
        return pickle.loads(data)
    
    async def send(self, client_id: str, data):
        # SEND message
        response_bytes = pickle.dumps(data)
        response_size = len(response_bytes)
        message = struct.pack("Q",response_size)+response_bytes
        # Send the response data in chunks
        for offset in range(0, len(message), CHUNK_SIZE):
            chunk = message[offset:offset + CHUNK_SIZE]
            await self.clients[client_id]["ws"].send_bytes(chunk)

server = Server()

@app.get("/api_get_portforwardpy")
async def get_uuid(request: Request):
    idx_bytes = secrets.token_bytes(8)
    hashed_key = hashlib.sha256(idx_bytes).digest()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(idx_bytes) + padder.finalize()
    cipher = Cipher(algorithms.AES(hashed_key), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_idx = encryptor.update(padded_data) + encryptor.finalize()
    hex_string = ''.join(['{:02x}'.format(byte) for byte in encrypted_idx])
    uid = uuid.UUID(f"{hex_string[:8]}-{hex_string[8:12]}-{hex_string[12:16]}-{hex_string[16:20]}-{hex_string[20:]}")
    # uid = '127.0' # TODO TESTING
    return JSONResponse(content={"client_id": str(uid)})

# WebSocket endpoint
@app.websocket("/api_portforwardpy/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await server.handle_client(websocket, client_id)

@app.get("/{url:path}")
@app.post("/{url:path}")
@app.delete("/{url:path}")
@app.put("/{url:path}")
async def forward_request(url: str, request: Request):
    # base_domain = '.'.join(urlparse(str(request.url)).netloc.split('.')[-DOMAIN_DEPTH:])
    client_id = '.'.join(urlparse(str(request.url)).netloc.split('.')[:-DOMAIN_DEPTH])
    client = server.clients.get(client_id)
    if not client:
        return JSONResponse(content={"error": "No client connected"}, status_code=400)
    else:
        data = await request.body()
        await server.send(client_id, {
                                        'method': request.method,
                                        'url': url,
                                        'headers': dict(request.headers),
                                        'data': data
                                    })
        data = await server.recv(client_id)
        
        # Create a FastAPI Response object
        fastapi_response = Response(content=data['body'], status_code=data['status'])

        # Set headers in the FastAPI Response object
        for header, value in data['headers'].items():
            fastapi_response.headers[header] = value
            
        return fastapi_response
        

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
    