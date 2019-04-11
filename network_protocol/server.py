import errno
from socket import *
from struct import pack


class ServerProtocol:

    def __init__(self):
        self.socket = None
        self.connection = None

    def listen(self, server_ip, server_port):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.settimeout(1)   # accept calls will return socket.timeout after 1 second
        self.socket.bind((server_ip, server_port))
        self.socket.listen(1)

    def accept(self):
        (self.connection, addr) = self.socket.accept()
        return addr

    def send_image(self, image_data):
        # Before sending the actual data, we need to send the size (in bytes) of the data
        # Use struct to ensure a consistent endianness on the length.
        # Specifically, '>' indicates big-endian, 'Q' means unsigned long long
        length = pack('>Q', len(image_data))

        # Send the size first, then the data
        self.connection.sendall(length)
        self.connection.sendall(image_data)

        # Receive an acknowledgement from the client
        ack = self.connection.recv(1)

    def close_client(self, shutdown=True):
        if (self.connection is not None):
            if shutdown:
                self.connection.shutdown(SHUT_WR)
            self.connection.close()
            self.connection = None

    def close(self, shutdown=True):
        self.close_client(shutdown)
        if shutdown:
            self.socket.shutdown(SHUT_WR)
        self.socket.close()
        self.socket = None

