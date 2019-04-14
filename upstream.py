import cv2
import sys
import socket
import getopt
import errno
import threading
from Queue import Queue, Empty
from network_protocol.server import ServerProtocol

camera_idx = 0
address = '127.0.0.1'
port = 54321
nocolor = False


class Upstreamer(threading.Thread):
    """ Stream a video to another host. """

    def __init__(self, name, addr, port, nocolor):
        threading.Thread.__init__(self)
        self.name = name
        self.addr = addr
        self.port = port
        self.nocolor = nocolor
        self.Q = Queue(1)
        self.__stop_event = threading.Event()
        self.sp = ServerProtocol()
        try:
            self.sp.listen(self.addr, self.port)
        except Exception:
            print "Can't listen for connections on the specified address/port"
            self.sp.close(False)
            raise Exception
            
    def stop(self):
        self.__stop_event.set()
        
    def stopped(self):
        return self.__stop_event.is_set()
        
    def close(self):
        self.stop()
        self.join()
        
    def stream_frame(self, frame):
        """ Store a new frame to be streamed """
        if not self.Q.full():
            self.Q.put(frame)
        
    def run(self):
        print 'Starting upstream'
        while not self.stopped():
        
            # Attempt to establish a connection with any client
            print 'Waiting for connections...'
            cl_addr = None
            while cl_addr is None:
                if self.stopped():
                    break
                try:
                    cl_addr = self.sp.accept()  # timeouts every 1 second
                except socket.timeout:
                    pass
            if cl_addr is None:     # may happen if the thread was stopped
                break
            print "Got connection from ", cl_addr
            
            # Stream data as long as the socket stays alive
            while not self.stopped():
                try:
                    img = self.Q.get(block=True, timeout=2)

                    # Convert the frame to B/W (optional)
                    if self.nocolor:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                    # Send the frame
                    _, img_data = cv2.imencode('.jpg', img)
                    self.sp.send_image(img_data)
                except Empty:
                    break
                except socket.error as se:
                    if (se.errno == errno.ECONNRESET) or (se.errno == errno.EPIPE):
                        print 'Closing connection with client'
                    else:
                        print 'Closing connection due to unexpected exception: ', se
                    break
            # Close connection with the client
            self.sp.close_client(False)
        # Stop accepting connections 
        self.sp.close(False)
        print 'All connections closed'


def parse_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ha:p:v:", ["help", 'addr=', 'port=', 'videocamera='])
    except getopt.GetoptError:
        print 'Check the README file for info about usage.'
        sys.exit(2)

    for o, a in opts:
        if o in ("-a", "--addr"):
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
        elif o in ("-v", "--videocamera"):
            global camera_idx
            camera_idx = int(a)
        elif o in ("-h", "--help"):
            print "Check the README file for info about options."
            sys.exit()
        else:
            assert False, "unhandled option"


if __name__ == "__main__":

    parse_options()

    # Initialize stuff
    print 'Initializing camera'
    cap = cv2.VideoCapture(camera_idx)
    up = Upstreamer("upstreaming thread", address, port, nocolor)
    up.start()

    # Acquire, process and show frames
    try:
        while True:
            ret, frame = cap.read()
            if ret:
                up.stream_frame(frame)
            else:
                print 'Failed to read from the camera\nHalting the streaming'
                break
    except KeyboardInterrupt:
        pass

    up.close()
    cap.release()
    print 'All threads stopped'
