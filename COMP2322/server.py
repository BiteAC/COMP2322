import socket
import threading
import os
import time
from email.utils import formatdate, parsedate_to_datetime
import urllib.parse

# Server configuration
HOST = '0.0.0.0'  # You may run the server on your own computer, using the IP address of 127.0.0.1.
PORT = 8080
LOG_FILE = 'server.log'
WEB_ROOT = './www'  # Directory where your html and image files will be stored

# Status codes mapping
STATUS_CODES = {
    200: 'OK',
    304: 'Not Modified',
    400: 'Bad Request',
    403: 'Forbidden',
    404: 'File Not Found'
}


def write_log(client_ip, request_file, response_status):

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_entry = f"[{current_time}] IP: {client_ip} | Requested File: {request_file} | Status: {response_status}\n"
    print(log_entry.strip())
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error writing to log: {e}")


def handle_client(client_socket, client_address): #Function to handle a single client connection in a separate thread.

    client_ip = client_address[0]

    while True:  # Loop to support HTTP persistent connection (keep-alive)
        try:
            client_socket.settimeout(10.0)  # Timeout for keep-alive connections
            request_data = client_socket.recv(4096).decode('utf-8')

            if not request_data:
                break

            lines = request_data.split('\r\n')
            request_line = lines[0]

            # Parse the request to determine the specific file being requested
            parts = request_line.split()
            if len(parts) != 3:
                send_error_response(client_socket, 400, client_ip, "Bad Request")
                break

            method, path, version = parts

            # Support GET and HEAD commands
            if method not in ['GET', 'HEAD']:
                send_error_response(client_socket, 400, client_ip, path)
                break

            # Parse headers
            headers = {}
            for line in lines[1:]:
                if line == '':
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            # Handle Connection header field for keep-alive and close
            connection_header = headers.get('connection', 'close').lower()
            keep_alive = (connection_header == 'keep-alive')

            # Determine file path
            if path == '/':
                path = '/index.html'
            path = urllib.parse.unquote(path)
            filepath = os.path.join(WEB_ROOT, path.lstrip('/'))

            # Check if file exists -> 404 File Not Found
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                send_error_response(client_socket, 404, client_ip, path)
                if not keep_alive: break
                continue

            # Check file reading permissions -> 403 Forbidden
            if not os.access(filepath, os.R_OK):
                send_error_response(client_socket, 403, client_ip, path)
                if not keep_alive: break
                continue

            # Handle Last-Modified and If-Modified-Since
            mtime = os.path.getmtime(filepath)
            last_modified_date = formatdate(mtime, usegmt=True)

            if_modified_since = headers.get('if-modified-since')
            if if_modified_since:
                try:
                    ims_datetime = parsedate_to_datetime(if_modified_since)
                    if mtime <= ims_datetime.timestamp():
                        # 304 Not Modified
                        send_response(client_socket, 304, client_ip, path, method, keep_alive=keep_alive)
                        if not keep_alive: break
                        continue
                except (TypeError, ValueError):
                    pass  # Invalid date format, proceed to send file

            # 200 OK - Send the file
            content_type = 'text/html'
            if filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif filepath.endswith('.png'):
                content_type = 'image/png'
            elif filepath.endswith('.txt'):
                content_type = 'text/plain'

            send_response(client_socket, 200, client_ip, path, method, filepath, content_type, last_modified_date,
                          keep_alive)

            if not keep_alive:
                break  # Close non-persistent connection

        except socket.timeout:
            break  # Timeout on keep-alive
        except Exception as e:
            print(f"Server error: {e}")
            break

    client_socket.close()


def send_response(client_socket, status_code, client_ip, requested_file, method, filepath=None,
                  content_type='text/html', last_modified=None, keep_alive=False):
    """
    Create and send an HTTP response message.
    """
    status_text = STATUS_CODES.get(status_code, 'Unknown')
    response_headers = f"HTTP/1.1 {status_code} {status_text}\r\n"

    connection_str = "keep-alive" if keep_alive else "close"
    response_headers += f"Connection: {connection_str}\r\n"

    body = b""
    if status_code == 200 and filepath:
        with open(filepath, 'rb') as f:
            body = f.read()
        response_headers += f"Content-Type: {content_type}\r\n"
        response_headers += f"Content-Length: {len(body)}\r\n"
        if last_modified:
            response_headers += f"Last-Modified: {last_modified}\r\n"

    response_headers += "\r\n"

    # Send headers
    client_socket.sendall(response_headers.encode('utf-8'))
    # Send body only if method is GET and status is 200
    if method == 'GET' and status_code == 200:
        client_socket.sendall(body)

    write_log(client_ip, requested_file, f"{status_code} {status_text}")


def send_error_response(client_socket, status_code, client_ip, requested_file):
    send_response(client_socket, status_code, client_ip, requested_file, 'GET', keep_alive=False)


def start_server():

    # Create the root directory for web files if it doesn't exist
    if not os.path.exists(WEB_ROOT):
        os.makedirs(WEB_ROOT)
        # Create a sample index.html for testing
        with open(os.path.join(WEB_ROOT, 'index.html'), 'w') as f:
            f.write("<html><body><h1>Welcome to Comp 2322 Web Server!</h1></body></html>")

    # Create a connection socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Server is listening on {HOST}:{PORT}...")

        while True:
            # Create a connection socket when contacted by a client
            client_socket, client_address = server_socket.accept()
            # Multi-threaded: create a new thread for each connection
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()

    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server_socket.close()


if __name__ == '__main__':
    start_server()