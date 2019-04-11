import cv2
import os
import numpy as np
import getopt, sys
import socket
import errno
from network_protocol.client import ClientProtocol

addr = '127.0.0.1'      # default IP address of the streamer
port = 54321            # default port of the streamer
image_folder = 'img'    # default folder for video recording
video_name = 'stream.avi'   # default video name
fps = 10                # frame per second of the video
record = False          # record video or not (default)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hra:p:", \
                     ["help", "record", 'addr=', 'port='])
    except getopt.GetoptError as err:
        print 'Check the README file for info about usage.'
        sys.exit(2)
    for o, a in opts:
        if o in ("-r", "--record"):
            global record
            record = True
        elif o in ("-a", "--addr"):
            global addr
            addr = a
            try:
                socket.inet_aton(addr)
            except socket.error:
                assert False, "invalid IP address"
        elif o in ("-p", "--port"):
            global port
            port = int(a)
            assert (port > 1024 and port <= 65535), "invalid port"
        elif o in ("-h", "--help"):
            print "Check the README file for info about options."
            sys.exit()
        else:
            assert False, "unhandled option"

    cp = ClientProtocol()
    
    try:
        print 'Connecting with the downstream server...'
        cp.connect(addr, port)
        print 'Connected!'
    except socket.error as se:
        if se.errno == errno.ECONNREFUSED:
            print 'Connection refused. Is the other side already streaming?'
        else:
            print 'Failed to connect.'
        cp.close(False)
        sys.exit(1)
    
    try:
        while(True):
            file_num, str_data = cp.recv_image()
            if file_num == None:
                break;
            else:
                # Convert the received data to video frame format
                numpy_data = np.fromstring(str_data, dtype = np.uint8)
                img_data = cv2.imdecode(numpy_data, cv2.CV_LOAD_IMAGE_COLOR)
                # Display the frame
                cv2.imshow('Streaming', img_data)
                cv2.waitKey(1)
                if(record):
                    # Write the received image to a file whose name is the index of the image
                    with open(os.path.join(image_folder, '%06d.jpg' % file_num), 'w') as fp:
                        fp.write(str_data)
    except KeyboardInterrupt:
        pass
    finally:
        cp.close()
        print 'Connection closed'

    # Assemble the video if the --record option was specified
    if(record):
        images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
        frame = cv2.imread(os.path.join(image_folder, images[0]))
        height, width, layers = frame.shape

        video = cv2.VideoWriter(video_name, cv2.cv.CV_FOURCC('M','J','P','G'), fps, (width,height))

        for image in sorted(images):
            video.write(cv2.imread(os.path.join(image_folder, image)))
        video.release()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
