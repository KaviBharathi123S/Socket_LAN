# LAN Chat & File Transfer Application

A browser-based real-time chat and file-sharing application built using Python, FastAPI, Uvicorn, and WebSockets. It enables multiple users to communicate and share files over a Local Area Network (LAN).

## Features
- Real-time, two-way chat
- Multiple client connections
- File sharing with chunked binary transfer
- File downloads through HTTP
- Browser-based interface
- LAN communication between computers

## Technologies
- Python
- FastAPI & Uvicorn
- WebSocket
- HTML, CSS & JavaScript
- TCP/IP

## How to Run

1. Install dependencies:

   ```bash
   pip install fastapi uvicorn
   ```

2. Start the server:

   ```bash
   python server.py
   ```

3. Open on the server computer:

   `http://localhost:8000`

4. To connect from another computer, find the server's IPv4 address using `ipconfig` and open:

   `http://YOUR_IPV4:8000`

   Both computers must be connected to a network that allows communication between them. Windows Firewall may need an inbound rule for TCP port `8000`.

## Concepts Learned
- Client-server communication
- IP addresses and port numbers
- TCP/IP networking
- HTTP and WebSockets
- Multiple clients and real-time messaging
- Chunked file transfer
- Firewall configuration and network troubleshooting

## Note
This project is intended for learning and LAN testing. HTTP communication is unencrypted, so additional security measures are needed before public deployment.
