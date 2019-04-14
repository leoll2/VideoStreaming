import cv2
import os
import numpy as np
import getopt
import sys
import socket
import threading
import errno
from Queue import Queue, Full
from network_protocol.client import ClientProtocol

address = '127.0.0.1'       # default IP address of the streamer
port = 54321                # default port of the streamer
image_folder = 'img/'       # default folder for video recording
video_name = 'stream.avi'   # default video name
fps = 10                    # frame per second of the video
record = False              # record video or not (default)


class Downstreamer(threading.Thread):
    """ Receive a streamed video from another host """

    def __init__(self, name, addr, port, record, path=None):
        threading.Thread.__init__(self)
        self.name = name
        self.addr = addr
        self.port = port
        self.record = record
        self.path = path
        self.Q = Queue(1)
        self.__stop_event = threading.Event()
        self.cp = ClientProtocol()
        try:
            print 'Connecting with the upstream server...'
            self.cp.connect(addr, port)
            print 'Connected!'
        except socket.error as se:
            if se.errno == errno.ECONNREFUSED:
                print 'Connection refused. Is the other side already streaming?'
            else:
                print 'Failed to connect.'
            self.cp.close(False)
            raise Exception

    def stop(self):
        self.__stop_event.set()

    def stopped(self):
        return self.__stop_event.is_set()

    def close(self):
        self.stop()
        self.join()

    def receive_frame(self):
        """ Get a new frame from the stream """
        if not self.Q.empty():
            return self.Q.get()
        else:
            return None

    def run(self):

        while not self.stopped():
            file_num, str_data = self.cp.recv_image()
            if file_num is None:    # TODO: verify
                break
            else:
                # Convert the received data to video frame format
                numpy_data = np.fromstring(str_data, dtype=np.uint8)
                img_data = cv2.imdecode(numpy_data, cv2.IMREAD_COLOR)
                # Share the new frame (if receiver is ready)
                try:
                    self.Q.put(img_data, block=False)
                except Full:
                    pass
                if record:
                    # Write the received image to a file whose name is the index of the image
                    with open(os.path.join(image_folder, '%06d.jpg' % file_num), 'w') as fp:
                        fp.write(str_data)
        print 'exitloop'
        self.cp.close()
        print 'Connection closed'


def parse_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hra:p:", ["help", "record", 'addr=', 'port='])
    except getopt.GetoptError:
        print 'Check the README file for info about usage.'
        sys.exit(2)

    for o, a in opts:
        if o in ("-r", "--record"):
            global record
            record = True
        elif o in ("-a", "--addr"):
            global address
            address = a
            try:
                socket.inet_aton(address)
            except socket.error:
                assert False, "invalid IP address"
        elif o in ("-p", "--port"):
            global port
            port = int(a)
            assert (1024 < port <= 65535), "invalid port"
        elif o in ("-h", "--help"):
            print "Check the README file for info about options."
            sys.exit()
        else:
            assert False, "unhandled option"


if __name__ == "__main__":

    parse_options()

    path = os.path.join(image_folder, video_name)
    down = Downstreamer("downstreaming thread", address, port, record, path)
    down.start()

    # Acquire and show frames
    try:
        while True:
            frame = down.receive_frame()
            if frame is not None:
                # Display the frame
                cv2.imshow('Streaming', frame)
                cv2.waitKey(1)
    except KeyboardInterrupt:
        print 'keyboardinterrupt'
        pass

    down.close()
    cv2.destroyAllWindows()
    print 'Closed streaming'
