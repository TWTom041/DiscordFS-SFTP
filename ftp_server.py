from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from fstpy.filesystems import AbstractedFS

class InMemoryFileSystem:
    def __init__(self):
        self.fs = {}

    def add_file(self, path, content):
        self.fs[path] = content

    def get_file_content(self, path):
        return self.fs.get(path, b'')

    def list_files(self, path):
        return [name for name in self.fs if name.startswith(path)]

def create_ftp_server():
    authorizer = DummyAuthorizer()
    authorizer.add_user("username", "password", "/", perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer

    fs = InMemoryFileSystem()

    handler.abstracted_fs = fs

    server = FTPServer(("127.0.0.1", 21), handler)

    return server

if __name__ == "__main__":
    ftp_server = create_ftp_server()

    print("FTP Server is running. Press Ctrl+C to stop.")
    try:
        ftp_server.serve_forever()
    except KeyboardInterrupt:
        print("FTP Server shutting down.")
        ftp_server.close_all()
