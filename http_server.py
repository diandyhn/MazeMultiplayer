import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import json

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        self.types['.json'] = 'application/json'
        
    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append("HTTP/1.0 {} {}\r\n".format(kode, message))
        resp.append("Date: {}\r\n".format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: mazeserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n".format(len(messagebody)))
        
        # Add CORS headers for web clients
        resp.append("Access-Control-Allow-Origin: *\r\n")
        resp.append("Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n")
        resp.append("Access-Control-Allow-Headers: Content-Type\r\n")
        
        for kk in headers:
            resp.append("{}:{}\r\n".format(kk, headers[kk]))
        resp.append("\r\n")

        response_headers = ''
        for i in resp:
            response_headers = "{}{}".format(response_headers, i)
            
        # Convert messagebody to bytes if needed
        if type(messagebody) is not bytes:
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        return response

    def proses(self, data):
        requests = data.split("\r\n")
        baris = requests[0]
        all_headers = [n for n in requests[1:] if n != '']
        
        # Extract request body for POST requests
        body = ""
        if "\r\n\r\n" in data:
            body_start = data.find("\r\n\r\n") + 4
            if body_start < len(data):
                body = data[body_start:]

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            if method == 'GET':
                object_address = j[1].strip()
                return self.http_get(object_address, all_headers)
            elif method == 'POST':
                object_address = j[1].strip()
                return self.http_post(object_address, all_headers, body)
            elif method == 'OPTIONS':
                # Handle CORS preflight
                return self.response(200, 'OK', '', {'Content-Type': 'text/plain'})
            else:
                return self.response(400, 'Bad Request', '', {})
        except IndexError:
            return self.response(400, 'Bad Request', '', {})

    def http_get(self, object_address, headers):
        files = glob('./*')
        thedir = './'
        
        if object_address == '/':
            return self.response(200, 'OK', 'Maze Game HTTP Server', dict())
        
        if object_address == '/status':
            return self.response(200, 'OK', 'Server is running', 
                               {'Content-Type': 'text/plain'})
        
        object_address = object_address[1:]
        if thedir + object_address not in files:
            return self.response(404, 'Not Found', '', {})
            
        fp = open(thedir + object_address, 'rb')
        isi = fp.read()
        fp.close()
        
        fext = os.path.splitext(thedir + object_address)[1]
        content_type = self.types.get(fext, 'application/octet-stream')
        
        headers = {'Content-type': content_type}
        return self.response(200, 'OK', isi, headers)

    def http_post(self, object_address, headers, body):
        headers = {}
        isi = "kosong"
        return self.response(200, 'OK', isi, headers)

    def create_json_response(self, data, status_code=200, status_message='OK'):
        """Helper method to create JSON responses"""
        json_data = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        return self.response(status_code, status_message, json_data, headers)

if __name__ == "__main__":
    httpserver = HttpServer()
    d = httpserver.proses('GET /status HTTP/1.0')
    print(d)