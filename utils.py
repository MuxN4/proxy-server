import socket
from urllib.parse import urlparse
from logger import logger

def pasre_http_header(header): # Skips the first line
    header_lines = header.split("\r\n")
    parsed_header = {}
    for line in header_lines[1:]:
        if line:
            key, value = line.split(":", 1)
            parsed_header[key.lower()] = value

    return parsed_header

def extract_host_port(url):
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    return host, port

def create_connection(host, port, timeout=10):
    try:
        conn = socket.create_connection((host, port), timeout=timeout)
        return conn
    except socket.error as e:
        logger.error(f"Failed to connect to {host}:{port}. Error: {e}")
        return None
    
def send_data(conn, data):
    try:
        conn.sendall(data)
    except socket.error as e:
        logger.error(f"Failed to send data. Error: {e}")
        return False
    return True

def receive_data(conn, buffer_size=4096):
    try:
        data = conn.recv(buffer_size)
        return data
    except socket.error as e:
        logger.error(f"Failed to receive data. Error: {e}")
        return None
    
def close_connection(conn):
    try:
        conn.close()
    except socket.error as e:
        logger.error(f"Error while closing connection: {e}")