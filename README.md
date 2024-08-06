# Simple HTTP/HTTPS Proxy Server

This project creates a basic proxy server in Python. It acts as a middleman for requests from clients trying to get resources from other servers. The proxy supports both HTTP and HTTPS, handles requests and responses, can tunnel connections for HTTPS, and has a simple caching feature.

## Features

 - Handles both HTTP and HTTPS protocols
 - Uses multiple threads to manage several client connections at once
 - Includes a basic in-memory cache to improve performance
 - Provides detailed logging for debugging and monitoring
 - Allows configurable host and port settings

## Installation

1. Clone this repository 
```sh
    git clone https://github.com/MuxN4/proxy-server.git
```

2. No additional dependencies are required as the script uses Python  standard libraries.

## Usage
1. Open a terminal and navigate to the directory containing `proxy_server.py`.
2. Run the proxy server with:

```sh
    python3 main.py
```

3. By default, the server will start on localhost (127.0.0.1) and port 8080. You can change these settings in the script if needed.

4. Configure your client (browser or application) to use the proxy:

   - Proxy Address: 127.0.0.1 (or the IP address where you're running the script)
   - Port: 8080

5. To test using curl:

```sh
    curl -v -x http://localhost:8080 http://example.com
```

## Configuration
You can change these variables in the script to adjust the server's behavior:

 - HOST: The address on which the proxy server will listen (default: 'localhost')
 - PORT: The port on which the proxy server will listen (default: 8080)
 - BUFFER_SIZE: Size of the buffer for receiving data (default: 8192 bytes)
 - CONNECTION_TIMEOUT: Timeout for connections in seconds (default: 5 seconds)

## Logging

The proxy server uses Python's logging module to provide detailed logs. By default, it's set to DEBUG level. You can change the logging level in the script if needed.

## Limitations and Future Improvements

 - The current implementation uses a simple in-memory cache. For production use, consider a more robust caching mechanism.
 - HTTPS handling is basic and does not include certificate verification.
 - The proxy does not currently support authentication.
 - Performance optimizations may be needed for high-traffic scenarios.

## Contributing
Contributions are welcome to improve the proxy server. Feel free to submit pull requests or open issues to discuss potential improvements.

## License
[Specify your chosen license here, e.g., MIT, GPL, etc.]

## Disclaimer
This proxy server is a basic implementation. It may not be suitable for production environments without further enhancements and security considerations.
