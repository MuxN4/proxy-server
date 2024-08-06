import socket
from threading import Thread
from urllib.parse import urlparse
from logger import logger
from config import BUFFER_SIZE, CONNECTION_TIMEOUT
from utils import parse_http_header, extract_host_port, create_connection, send_data, receive_data, close_connection
from cache import cache

class ProxyHandler:
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address
        self.target_socket = None

    def handle_client_request(self):
        try:
            self.client_socket.settimeout(CONNECTION_TIMEOUT)
            request = self.receive_client_request()
            if not request:
                logger.warning("Received empty request")
                return

            method, url, version, headers = self.parse_request(request)
            logger.info(f"Received request: {method} {url} {version}")

            if method == 'CONNECT':
                self.handle_https_request(url)
            else:
                self.handle_http_request(method, url, version, headers, request)
        except socket.timeout:
            logger.warning(f"Connection from {self.client_address} timed out")
        except Exception as e:
            logger.error(f"Error handling request from {self.client_address}: {e}")
            logger.exception("Exception details:")
        finally:
            self.close_connections()

    def receive_client_request(self):
        request = b''
        while b'\r\n\r\n' not in request:
            chunk = receive_data(self.client_socket, BUFFER_SIZE)
            if not chunk:
                break
            request += chunk
        logger.debug(f"Received raw request: {request[:100]}...")  # Log the first 100 bytes
        return request

    def parse_request(self, request):
        try:
            request_lines = request.decode('utf-8').split('\r\n')
            method, full_url, version = request_lines[0].split()
            headers = parse_http_header('\r\n'.join(request_lines[1:]))
            
            parsed_url = urlparse(full_url)
            if parsed_url.scheme:
                url = full_url
            else:
                url = f"http://{headers.get('host', '')}{full_url}"
            
            return method, url, version, headers
        except Exception as e:
            logger.error(f"Error parsing request: {e}")
            raise

    def handle_https_request(self, url):
        host, port = extract_host_port(url)
        try:
            self.target_socket = create_connection(host, port)
            if not self.target_socket:
                logger.error(f"Failed to create connection to {host}:{port}")
                return

            self.client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            self.tunnel_traffic(self.client_socket, self.target_socket)
        except Exception as e:
            logger.error(f"Error handling HTTPS request: {e}")
            logger.exception("Exception details:")

    def handle_http_request(self, method, url, version, headers, request):
        cache_key = f"{method}:{url}"
        cached_response = cache.get(cache_key)

        if cached_response:
            logger.info(f"Cache hit for {url}")
            self.send_cached_response(cached_response)
            return

        host, port = extract_host_port(url)
        try:
            self.target_socket = create_connection(host, port)
            if not self.target_socket:
                logger.error(f"Failed to create connection to {host}:{port}")
                return

            modified_request = self.modify_request(request, headers)
            send_data(self.target_socket, modified_request)
            
            response = self.receive_response()
            if not response:
                logger.error("Received empty response from target server")
                return

            if self.is_cacheable(method, response):
                cache.set(cache_key, response)
            
            self.forward_response(response)
        except Exception as e:
            logger.error(f"Error handling HTTP request: {e}")
            logger.exception("Exception details:")

    def receive_response(self):
        response = b''
        while True:
            chunk = receive_data(self.target_socket, BUFFER_SIZE)
            if not chunk:
                break
            response += chunk
        logger.debug(f"Received response: {response[:100]}...")  # Log the first 100 bytes
        return response

    def forward_response(self, response):
        try:
            send_data(self.client_socket, response)
            logger.info("Response forwarded to client")
        except Exception as e:
            logger.error(f"Error forwarding response to client: {e}")

    def send_cached_response(self, response):
        try:
            send_data(self.client_socket, response)
            logger.info("Cached response sent to client")
        except Exception as e:
            logger.error(f"Error sending cached response to client: {e}")

    def is_cacheable(self, method, response):
        if method != 'GET':
            return False
        
        headers = parse_http_header(response.split(b'\r\n\r\n')[0].decode('utf-8'))
        cache_control = headers.get('cache-control', '').lower()
        
        if 'no-store' in cache_control or 'private' in cache_control:
            return False
        if 'max-age=0' in cache_control:
            return False
        
        return True

    def modify_request(self, request, headers):
        request_lines = request.decode('utf-8').split('\r\n')
        method, path, version = request_lines[0].split()
        
        parsed_url = urlparse(path)
        new_path = parsed_url.path
        if parsed_url.query:
            new_path += '?' + parsed_url.query
        
        request_lines[0] = f"{method} {new_path} {version}"
        
        headers_to_remove = ['proxy-connection', 'proxy-authorization']
        filtered_headers = [line for line in request_lines[1:] if line.split(':')[0].lower() not in headers_to_remove]
        
        modified_request = '\r\n'.join([request_lines[0]] + filtered_headers + ['', ''])
        return modified_request.encode('utf-8')

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

    def close_connections(self):
        close_connection(self.client_socket)
        if self.target_socket:
            close_connection(self.target_socket)
        logger.info("Connections closed")

def run_proxy(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    logger.info(f"Proxy server is listening on {host}:{port}")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            logger.info(f"Accepted connection from {client_address}")
            handler = ProxyHandler(client_socket, client_address)
            client_thread = Thread(target=handler.handle_client_request)
            client_thread.start()
        except Exception as e:
            logger.error(f"Error accepting connection: {e}")
