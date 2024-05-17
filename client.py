import argparse
import aiohttp
import asyncio
import pickle
import struct
import requests
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Constants
CHUNK_SIZE = 1024 * 1024 * 4  # 4 MB
PAYLOAD_SIZE = struct.calcsize("Q")  # Header size which contains size of message

console = Console()
status_data = {
    "session_status": "offline",
    "account": "User",
    "version": "1.0.0",
    "region": "Unknown",
    "latency": "Unknown",
    "web_interface": "Under development",
    "forwarding": "Unknown"
}

def display_status():
    console.clear()
    panel = Panel(
        Text.from_markup(
            f"[bold cyan]Session Status:[/bold cyan] {status_data['session_status']}\n"
            f"[bold cyan]Account:[/bold cyan] {status_data['account']}\n"
            f"[bold cyan]Version:[/bold cyan] {status_data['version']}\n"
            f"[bold cyan]Region:[/bold cyan] {status_data['region']}\n"
            f"[bold cyan]Latency:[/bold cyan] {status_data['latency']}\n"
            f"[bold cyan]Web Interface:[/bold cyan] {status_data['web_interface']}\n"
            f"[bold cyan]Forwarding:[/bold cyan] {status_data['forwarding']}"
        ),
        title="Ngrok-like Tunnel",
        border_style="bold green"
    )
    console.print(panel)

async def client_connect(url, server_url, server_protocol):
    console.print("Trying to connect to the server...", style="bold yellow")
    try:
        response = requests.get(f'{server_protocol}://{server_url}/api_get_portforwardpy')
        response.raise_for_status()
        client_id = response.json()['client_id']
        status_data["forwarding"] = f"{server_protocol}://{client_id}.{server_url} -> {url}"
        status_data["session_status"] = "online"
        display_status()
    except requests.RequestException as e:
        console.print(f"Failed to get client_id: {e}", style="bold red")
        return

    console.print(f"Client ID: {client_id}", style="bold green")
    ws_url = f"wss://{server_url}/api_portforwardpy/{client_id}" if server_protocol == 'https' else f"ws://{server_url}/api_portforwardpy/{client_id}"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ws_url) as ws:
            console.print("Connection established", style="bold green")
            console.print(f'Your site {url} is live at {server_protocol}://{client_id}.{server_url}', style="bold blue")

            while True:
                try:
                    # Receive message
                    data = await ws.receive_bytes()
                    packed_msg_size = struct.unpack("Q", data[:PAYLOAD_SIZE])[0]
                    data = data[PAYLOAD_SIZE:]
                    while len(data) < packed_msg_size:
                        data += await ws.receive_bytes()
                    request_data = pickle.loads(data)

                    async with session.request(request_data['method'], f"{url}{request_data['url']}", headers=request_data['headers'], data=request_data['data']) as response:
                        console.print(f"{request_data['method']}: {url}{request_data['url']}", style="bold cyan")
                        response_content = await response.read()
                        # Create a dictionary with response data
                        response_data = {
                            'status': response.status,
                            'headers': dict(response.headers),
                            'body': response_content
                        }
                        # Send message
                        response_bytes = pickle.dumps(response_data)
                        response_size = len(response_bytes)
                        message = struct.pack("Q", response_size) + response_bytes
                        # Send the response data in chunks
                        for offset in range(0, len(message), CHUNK_SIZE):
                            chunk = message[offset:offset + CHUNK_SIZE]
                            await ws.send_bytes(chunk)

                except Exception as e:
                    console.print(f"Error processing request: {e}", style="bold red")
                    break

async def main(args):
    task1 = asyncio.create_task(client_connect(args.url, args.server_url, args.server_protocol))
    await asyncio.gather(task1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CLI tool for a ngrok-like service")
    parser.add_argument('--url', type=str, default='http://127.0.0.1:5000/', help='The local URL to be exposed')
    parser.add_argument('--server_url', type=str, default='dev.thefcraft.site', help='The server URL to connect to')
    parser.add_argument('--server_protocol', type=str, choices=['http', 'https'], default='https', help='The protocol to use for server connection (http or https)')

    args = parser.parse_args()
    
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        console.print('Quitting...', style="bold red")
        sys.exit(0)
        