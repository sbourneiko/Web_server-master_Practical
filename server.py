import socket
import datetime
from config import port, max_size, root
import os
import re
import threading
import magic


def nowDate():
    return datetime.datetime.utcnow().strftime(r"%a, %d %b %Y %H:%M:%S GMT")


def http_response(content, http_response_code, content_type):
    content_length = len(content)
    response = f"""HTTP/1.1 {http_response_code}
Date: {nowDate()}
Content-length: {content_length}
Server: SelfMadeServer v0.0.1
Content-type: {content_type}
Connection: retry-after

"""
    response = response.encode() + content
    return response


def get_resource(request):
    request = request.split("\r\n")
    request = request[0].split()[1]
    if request in ['\\', '/']:
        path = ["index.html"]
    else:
        path = re.split("[\\/]", request)
    allowed = bool(re.search("\.(html|css|js|pdf|txt|jpeg|jpg|png)$", path[-1]))
    print(allowed)
    return path, request, allowed


def parse_request(request, root="."):
    resource, http_path, allowed = get_resource(request)
    resource = os.path.join(root, *resource)
    content_type = "text/html"
    if allowed:
        try:
            with open(resource, "rb") as binaryfile:
                content = binaryfile.read(16777216)
            response_code = "200 OK"
            mime = magic.Magic(mime=True)
            content_type = mime.from_file(resource)
        except:
            content = b""
            response_code = "404 Not Found"
    else:
        content = b""
        response_code = "403 Forbidden"
    return content, http_path, response_code, content_type


def main(conn, addr, max_size, root):
    while True:
        request = conn.recv(max_size).decode()
        datenow = nowDate()
        if not request:
            continue
        content, resource, response_code, content_type = parse_request(request, root)
        log = "; ".join([str(i) for i in [datenow, addr, resource, response_code]])
        with LOCK:
            with open(LOGFILE, "a", encoding="utf8") as file:
                file.write(log + "\n")

        conn.send(http_response(content, response_code, content_type))


LOGFILE = "log.txt"
LOCK = threading.Lock()
sock = socket.socket()

print
sock.bind(('', port))
sock.listen(0)

while True:
    conn, addr = sock.accept()
    with LOCK:
        print("Подключен клиент ip: ", addr)

    threading.Thread(target=main, args=(conn, addr[0], max_size, root), daemon=True).start()
