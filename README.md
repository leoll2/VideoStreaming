# VideoStreaming
VideoStreaming is a lightweight Python library which allows you to stream images (i.e. video) between hosts on a network.
Its simplicity make it a perfect solution to include in small projects, where you just need something working out of the 
box, instead of having to reckon with unnecessarily complex frameworks.

### Requirements

The code is compatible and tested with Python 2.7. The library OpenCV (at least version 3.0) is required internally for
some image transformations.

### Nomenclature

- **upstream**: the host which stream videos/images. In other words, the sender.
- **downstream**: the client. In other words, the receiver.

## Usage

The streaming functions can be either used in standalone mode or called by an external application.
Standalone means that the code here in this repo can be directly launched to begin streaming, without the need to write
any additional line of code. On the other hand, if you need to embed it into another application, a friendly API is
available (see below).

### Standalone

This section describes the steps to rapidly setup a streaming between two hosts. As you are about to see, it is 
a very straightforward procedure.

First you need to launch the upstream on your streaming host:
```
python upstream.py <options>
```

Then you have to run the downstream on another client (e.g. another terminal, or another computer):
```
python downstream.py <options>
```

Options may be added to specify the network parameters or customize the behavior. A list of the available options is 
present here below.

#### Options 

##### Upstream   

* `-a <ip>` or `--addr <ip>`: Specify the IP address of the streamer. Default is 127.0.0.1.
* `-p <number>` or `--port <number>`: Specify the port of the streamer. Default is 54321.
* `-v <index>` or `--videocamera <index>`: Specify the index of the video camera to be used for image acquisition. 
Default is 1.
* `-d` or `--display`: Echo (display) the acquired images on the screen.

##### Downstream
* `-a <ip>` or `--addr <ip>`: Specify the IP address of the streamer. Default is 127.0.0.1.
* `-p <number>` or `--port <number>`: Specify the port of the streamer. Default is 54321.
* `-r` or `--record`: Record the streaming on a local file. (*Note: not fully implemented yet*)

### API

If you want to use VideoStream as part of a larger project, you may get advantage of its simple interface.

First of all, you need to include the appropriate modules in your source code, depending if you want to send (upstream) 
or receive (downstream) the images. Then, you simply instantiate an object of the corresponding class and call the 
relative methods to push/pop images to/from the stream.

##### Upstream


```
import upstream as us

# Allocate and enable the streamer
up = Upstreamer("myUpstreamer", address, port, nocolor)
up.start()

...
# Send a frame
up.stream_frame(frame)      # frame is OpenCV image (numpy array)
...
# Stop the streamer
up.close()
```

##### Downstream

```
import downstream as ds

# Start downloading the streaming
down = Downstreamer("downstreaming thread", address, port, record, path)
up.start()

...
# Get the latest frame from the streaming
frame = down.receive_frame()   # frame is OpenCV image (numpy array)
...
# Stop downloading
down.close()
```

## Notes

- The recording functionality is still work in progress
- API is currently supported for upstream only
- If you experience latency issues, it is likely due to your network rather than this application. Streaming images at
a lower resolution possibly mitigates the problem.

## Help us

Contributions or bug reports are always welcome. If you need help or have any suggestion, feel free to open an issue!