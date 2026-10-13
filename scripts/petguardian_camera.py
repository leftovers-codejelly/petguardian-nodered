import io
import logging
import socketserver
import time
from http import server
from threading import Condition, Thread

import cv2


CAMERA_INDEX = 0          # /dev/video0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30
JPEG_QUALITY = 80
PORT = 8000

PAGE = """\
<html>
<head>
    <title>Pet Guardian Camera</title>
</head>
<body>
    <h1>Pet Guardian - Live Camera</h1>
    <img src="/stream.mjpg" width="800">
</body>
</html>
"""


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class CameraThread(Thread):
    """Continuously grabs frames from the USB camera and publishes them as JPEGs."""

    def __init__(self, output):
        super().__init__(daemon=True)
        self.output = output
        self.running = True

        self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open USB camera at index {CAMERA_INDEX}. "
                "Check that it is plugged in (try: ls /dev/video*)."
            )

        # Ask the camera for MJPG, which allows higher resolutions/FPS over USB
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, FPS)
        # Keep the buffer small so the stream stays close to real time
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logging.info("Camera opened at %dx%d", w, h)

    def run(self):
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                logging.warning("Failed to read frame from camera, retrying...")
                time.sleep(0.5)
                continue

            ok, jpeg = cv2.imencode(".jpg", frame, encode_params)
            if ok:
                self.output.write(jpeg.tobytes())

    def stop(self):
        self.running = False
        self.join(timeout=2)
        self.cap.release()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Age", 0)
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type",
                "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()

            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame

                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")

            except Exception as e:
                logging.warning("Client disconnected: %s", str(e))

        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


logging.basicConfig(level=logging.INFO)

output = StreamingOutput()
camera = CameraThread(output)
camera.start()

try:
    address = ("", PORT)
    httpd = StreamingServer(address, StreamingHandler)

    print(f"Pet Guardian camera server running on port {PORT}")
    print("Press Ctrl+C to stop")

    httpd.serve_forever()

finally:
    camera.stop()
