import pickle
from socket import *
from struct import unpack


class ClientProtocol:

    def __init__(self):
        self.socket = None
        self.file_num = 0

    def connect(self, server_ip, server_port):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((server_ip, server_port))

    def close(self, shutdown=True):
        if (self.socket is not None):
            if shutdown:
                self.socket.shutdown(SHUT_WR)
            self.socket.close()
            self.socket = None

    def recv_image(self):
        try:
	        # Receive the size of the incoming data (as unsigned long long big-endian)
            bs = self.socket.recv(8)
            (length,) = unpack('>Q', bs)
            # If 0, then stop handling the stream
            if length == 0:
                print 'End of stream'
                return None, None
    
            frame_data = b''	# empty byte data
            # Receive the data in chunks of 4096 bytes
            while len(frame_data) < length:
                to_read = length - len(frame_data)
                frame_data += self.socket.recv(4096 if to_read > 4096 else to_read)

            # Send a 0 ack
            assert len(b'\00') == 1
            self.socket.sendall(b'\00')
            self.file_num += 1
            return self.file_num, frame_data
        except Exception as e:
            print e
            return None, None
