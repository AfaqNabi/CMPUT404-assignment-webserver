import socketserver
import enum
import os

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

BASE_DIR_PATH = "./www"
BASE_RESPONSE = "HTTP/1.1"
HOST, PORT = "127.0.0.1", 8080
BASE_URL = 'http://'+HOST+':'+str(PORT)
BYTES_PER_READ = 4096


class HTTP_RESPONSES(enum.Enum):
    OK = "200 OK"
    MOVED_PERMANENTLY = "301 Moved Permanently"
    METHOD_NOT_ALLOWED = "405 Method Not Allowed"
    NOT_FOUND = "404 Not Found"
    INTERNAL_SERVER_ERROR = "500 Internal Server Error"


# https://stackoverflow.com/questions/6803505/does-my-code-prevent-directory-traversal
def is_directory_traversal(file_name):
    current_directory = os.path.abspath(os.curdir)
    requested_path = os.path.relpath(file_name, start=current_directory)
    requested_path = os.path.abspath(requested_path)
    common_prefix = os.path.commonprefix([requested_path, current_directory])
    return common_prefix != current_directory


class MyWebServer(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(BYTES_PER_READ).strip()
        method, path = self.parse_request(self.data)
        filePath = BASE_DIR_PATH + path

        if method != 'GET':
            self.request.sendall(self.build_response(
                HTTP_RESPONSES.METHOD_NOT_ALLOWED, open('notAllowed.html', 'r').read()))

        if path[-1] != '/':
            print("Redirecting")
            self.request.sendall(self.build_response(
                HTTP_RESPONSES.MOVED_PERMANENTLY, filePath=path))
        elif os.path.isdir(filePath.rstrip('/')) and not is_directory_traversal(filePath):
            filePath += "index.html"
            self.request.sendall(self.build_response(
                HTTP_RESPONSES.OK, open(filePath.rstrip('/'), 'r').read(), filePath.rstrip('/')))
        elif os.path.isfile(filePath.rstrip('/')) and not is_directory_traversal(filePath):
            self.request.sendall(self.build_response(
                HTTP_RESPONSES.OK, open(filePath.rstrip('/'), 'r').read(), filePath.rstrip('/')))
        else:
            self.request.sendall(self.build_response(
                HTTP_RESPONSES.NOT_FOUND, open('notFound.html', 'r').read()))

    def build_response(self, code: HTTP_RESPONSES, fileData='', filePath='/'):
        response = BASE_RESPONSE + " "
        response += code.value + "\r\n"
        if filePath.endswith(".html") or filePath.endswith("/"):
            response += "Content-Type: text/html\r\n"
        elif filePath.endswith(".css"):
            response += "Content-Type: text/css\r\n"

        response += "Content-Length: " + str(len(fileData)) + "\r\n"
        if code == HTTP_RESPONSES.MOVED_PERMANENTLY:
            response += "Location: " + BASE_URL + filePath+"/\r\n"
        response += "\r\n"
        response += fileData
        return bytearray(response, 'utf-8')

    def parse_request(self, data):
        try:
            self.request_line = data.splitlines()[0].decode('utf-8')
        except Exception as e:
            print(e, data)
            return
        request_line = self.request_line.strip('\r\n')
        (self.request_method, self.path, self.request_version) = request_line.split()
        print(self.request_method, self.path, self.request_version)
        return self.request_method, self.path


if __name__ == "__main__":

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
