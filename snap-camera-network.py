#!/usr/bin/python3
import time
import socket
import argparse
import threading
import subprocess
import socketserver
try:
    from snapcamera.mode_options import (
        TAKE_PICTURE_AT,
        SEND_LAST_IMAGE_TO,
        MCAST_GRP,
        MCAST_PORT,
    )
except ImportError:
    # fallback on the original command if this script is not next to camera
    TAKE_PICTURE_AT = "take picture at "
    SEND_LAST_IMAGE_TO = "send last image to "
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007


TRIGGER_DELAY = 0.1  # seconds -- so that camera's can sync taking the photo
DEFAULT_NUM_CAMERAS = 1


class ImageTCPRequestHandler(socketserver.BaseRequestHandler):

    received_barrier = None

    def handle(self):
        camera_number = int(self.request.recv(16).decode('utf-8').strip())
        image_number = int(self.request.recv(16).decode('utf-8').strip())
        print("Receiving from camera {}: image{}".format(
            camera_number, image_number))
        file_name = "camera{}-image{}.jpg".format(camera_number, image_number)
        image_file = open(file_name, 'wb')
        data = self.request.recv(1024)
        while (data):
            image_file.write(data)
            data = self.request.recv(1024)
        self.received_barrier.wait()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def send_multicast(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(bytes(message, 'utf-8'), (MCAST_GRP, MCAST_PORT))


def trigger(number_of_cameras):
    pic_time = time.time() + TRIGGER_DELAY
    send_multicast(TAKE_PICTURE_AT + str(pic_time))


def getimages(number_of_cameras):
    # start the receiver server
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "", 0

    images_received_barrier = threading.Barrier(number_of_cameras + 1)

    class ImageTCPRequestHandlerWithBarrier(ImageTCPRequestHandler):
        received_barrier = images_received_barrier

    server = ThreadedTCPServer((HOST, PORT), ImageTCPRequestHandlerWithBarrier)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # tell each camera that they need to start sending me images
    ip, port = server.server_address
    send_multicast("{command}{ip}:{port}".format(
        command=SEND_LAST_IMAGE_TO, ip=get_my_ip(), port=port))

    images_received_barrier.wait()
    server.shutdown()


def get_my_ip():
    return run_cmd("hostname --all-ip-addresses")[:-1].strip()


def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--cameras', help="The number of cameras.", type=int)
    parser.add_argument(
        "command",
        choices=['trigger', 'getimages'],
        help="The command to run.")
    args = parser.parse_args()

    number_of_cameras = args.cameras if args.cameras else DEFAULT_NUM_CAMERAS

    commands = {
        'trigger': trigger,
        'getimages': getimages,
    }

    commands[args.command](number_of_cameras)
