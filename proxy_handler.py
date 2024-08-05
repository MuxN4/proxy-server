import socket
from threading import Thread
from logger import logger
from config import BUFFER_SIZE
from utils import parse_http_header, extract_host_port, create_connection, send_data, receive_data, close_connection

class ProxyHandler:
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address

    def handle_client_request(self):
        request = self.receive_client_request()
        if not request:
            return
        
        method, url, version, headers = self.parse_request(request)
        logger.info(f"Received request: {method} {url} {version}")

        if method == "CONNECT":
            self.handle_http_request(url)
        else:
            self.handle_http_request(method, url, version, headers, request)

    def receive_client_request(self):
        return receive_data(self.client_socket, BUFFER_SIZE)
    
    def parse_request(self, request):
        request_lines = request.decode('utf-8').split('\r\n')
        method, url, version = request_lines[0].split()
        headers = parse_http_header('\r\n'.join(request_lines[1:]))
        return method, url, version, headers

    def handle_https_request(self, url):
        host, port = extract_host_port(url)
        try:
            server_socket = create_connection(host, port)
            if not server_socket:
                return

            self.client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            self.tunnel_traffic(self.client_socket, server_socket)
        finally:
            close_connection(self.client_socket)
            if server_socket:
                close_connection(server_socket)

    def handle_http_request(self, method, url, version, headers, request):
        host, port = extract_host_port(url)
        try:
            server_socket = create_connection(host, port)
            if not server_socket:
                return

            send_data(server_socket, request)
            response = receive_data(server_socket, BUFFER_SIZE)
            while response:
                send_data(self.client_socket, response)
                response = receive_data(server_socket, BUFFER_SIZE)
        finally:
            close_connection(self.client_socket)
            if server_socket:
                close_connection(server_socket)

    def tunnel_traffic(self, client_socket, server_socket):
        def forward(source, destination):
            try:
                while True:
                    data = receive_data(source, BUFFER_SIZE)
                    if not data:
                        break
                    send_data(destination, data)
            except Exception as e:
                logger.error(f"Error in tunneling: {e}")

        client_thread = Thread(target=forward, args=(client_socket, server_socket))
        server_thread = Thread(target=forward, args=(server_socket, client_socket))

        client_thread.start()
        server_thread.start()

        client_thread.join()
        server_thread.join()

def run_proxy(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    logger.info(f"Proxy server is listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        logger.info(f"Accepted connection from {client_address}")
        handler = ProxyHandler(client_socket, client_address)
        client_thread = Thread(target=handler.handle_client_request)
        client_thread.start()

