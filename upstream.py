import cv2
import getopt, sys
import socket
import errno
import threading
from time import sleep
from Queue import Queue, Empty
from network_protocol.server import ServerProtocol

class Upstreamer(threading.Thread):
    ''' Stream a video to another host.
    '''

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
            self.sp.listen(addr, port)
        except:
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
        ''' Store a new frame to be streamed '''
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
                    frame = self.Q.get(block=True, timeout=2)

                    # Convert the frame to B/W (optional)
                    if (self.nocolor):
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    # Send the frame
                    ret, img_data = cv2.imencode('.jpg', frame)
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

if __name__ == "__main__":
    from ..video_processing.VideoProcessor import VideoProcessor
    
    # Initialize stuff
    print 'Initializing camera'
    vp = VideoProcessor(0, True)
    vp.start()
    up = Upstreamer("upstreaming thread", '127.0.0.1', 54321, False)
    up.start()
    
    # Main loop
    try:
        while(True):
            # Acquire, process and show frames
            frame = vp.acquire_processed_image()[0]
            up.stream_frame(frame)
    except KeyboardInterrupt:
        up.close()
        vp.close()
        print 'All threads stopped'

