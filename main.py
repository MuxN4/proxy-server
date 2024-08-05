import sys
from proxy_handler import run_proxy
from config import HOST, PORT
from logger import logger

def main():
    try:
        logger.info(f"Starting proxy server on {HOST} : {PORT}")
        run_proxy(HOST, PORT)
    except KeyboardInterrupt:
        logger.info("Proxy server stopped by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

