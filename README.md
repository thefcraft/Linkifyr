# Linkifyr Tunnel

This project implements a tunnel service similar to Ngrok, allowing users to expose their local servers to the internet securely. The implementation consists of a client-side application (`client.py`) and a server-side application (`app.py`) using FastAPI for handling WebSocket connections and HTTP requests.

## Features

- Dynamic urls like https://{client_id}.dev.thefcraft.site
- Securely exposes local servers to the internet.
- Handles HTTP/HTTPS requests and forwards them to the local server.
- Displays connection status and information using Rich for a better CLI experience.

## DEMO
```bash
python client.py --url http://127.0.0.1:5000/
```
```bash
╭─────────────────────────────────────────────────────── Linkifyr Tunnel ──────────────────────────────────────────────────────────╮
│ Session Status: online                                                                                                           │
│ Account: User                                                                                                                    │
│ Version: 1.0.0                                                                                                                   │
│ Region: Unknown                                                                                                                  │
│ Latency: Unknown                                                                                                                 │
│ Web Interface: Under development                                                                                                 │
│ Forwarding: https://62dc-f9-d0-9f65.dev.thefcraft.site -> http://127.0.0.1:5000/                                                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Client ID: 62dc-f9-d0-9f65
Connection established
Your site http://127.0.0.1:5000/ is live at https://62dc-f9-d0-9f65.dev.thefcraft.site
```

## Getting Started

### Prerequisites

- Python 3.7+
- `aiohttp`
- `requests`
- `fastapi`
- `uvicorn`
- `rich`
- `cryptography`

Install the required packages using pip:

```bash
pip install aiohttp requests fastapi uvicorn rich cryptography
```

### Client-Side Application

The client-side application (`client.py`) connects to the server, retrieves a unique client ID, and establishes a WebSocket connection for forwarding requests.

#### Usage

Run the client-side application with the following command:

```bash
python client.py --url http://127.0.0.1:5000/ --server_url dev.thefcraft.site --server_protocol https
```

#### Arguments

- `--url`: The local URL to be exposed (default: `http://127.0.0.1:5000/`).
- `--server_url`: The server URL to connect to (default: `dev.thefcraft.site`).
- `--server_protocol`: The protocol to use for server connection (`http` or `https`, default: `https`).

### Server-Side Application

The server-side application (`app.py`) uses FastAPI to handle incoming WebSocket connections and HTTP requests, forwarding them to the appropriate client.

#### Running the Server

Run the server-side application with the following command:

```bash
uvicorn app:app --host 0.0.0.0 --port 8080
```

#### dns config

use [wildcard domain](https://developers.cloudflare.com/dns/manage-dns-records/reference/wildcard-dns-records/)

[adding a wildcard custom domain](https://docs.render.com/custom-domains#adding-a-wildcard-custom-domain) on onrender

### Workflow

1. **Client Connection**: The client connects to the server and retrieves a unique client ID.
2. **WebSocket Connection**: The client establishes a WebSocket connection using the retrieved client ID.
3. **Request Forwarding**: The server forwards incoming HTTP requests to the connected client, which processes them and returns the response.

## Project Structure

```
.
├── client.py
├── app.py
└── README.md
```

- `client.py`: Contains the client-side logic for connecting to the server and forwarding requests.
- `app.py`: Contains the server-side logic for handling WebSocket connections and HTTP requests.
- `README.md`: Project documentation.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ngrok](https://ngrok.com/) for the inspiration.
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework.
- [Rich](https://github.com/Textualize/rich) for the beautiful CLI components.

For more details, visit the [GitHub repository](https://github.com/thefcraft/PortForwardPy).
