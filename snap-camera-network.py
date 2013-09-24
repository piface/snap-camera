#!/usr/bin/python3
import time
import socket
import argparse
import threading
import subprocess
import socketserver
try:
    from snapcamera.network import (
        TAKE_IMAGE_AT,
        SEND_LAST_IMAGE_TO,
        RECORD_VIDEO_FOR,
        SEND_LAST_VIDEO_TO,
        HALT_AT,
        REBOOT_AT,
        BACKLIGHT,
        RUN_COMMNAD,
        MCAST_GRP,
        MCAST_PORT,
    )
except ImportError:
    # fallback on the original command if this script is not next to camera
    TAKE_IMAGE_AT = "take image at "
    SEND_LAST_IMAGE_TO = "send last image to "
    RECORD_VIDEO_FOR = "record video for "
    SEND_LAST_VIDEO_TO = "send last video to "
    HALT_AT = "halt at "
    REBOOT_AT = "reboot at "
    BACKLIGHT = "backlight "  # on/off
    RUN_COMMNAD = "run command "
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007


TRIGGER_DELAY = 0.1  # seconds -- so that camera's can sync taking the photo
DEFAULT_NUM_CAMERAS = 1
DEFAULT_VIDEO_LENGTH = 5000  # milliseconds


class TCPRequestHandler(socketserver.BaseRequestHandler):

    received_barrier = None

    def handle(self, file_name):
        image_file = open(file_name, 'wb')
        data = self.request.recv(1024)
        while (data):
            image_file.write(data)
            data = self.request.recv(1024)
        self.received_barrier.wait()


class ImageTCPRequestHandler(TCPRequestHandler):
    def handle(self):
        camera_number = int(self.request.recv(16).decode('utf-8').strip())
        image_number = int(self.request.recv(16).decode('utf-8').strip())
        print("Receiving from camera {}: image{}".format(
            camera_number, image_number))
        file_name = "camera{}-image{}.jpg".format(camera_number, image_number)
        super().handle(file_name)


class VideoTCPRequestHandler(TCPRequestHandler):
    def handle(self):
        camera_number = int(self.request.recv(16).decode('utf-8').strip())
        video_number = int(self.request.recv(16).decode('utf-8').strip())
        print("Receiving from camera {}: video{}".format(
            camera_number, video_number))
        file_name = "camera{}-video{}.h264".format(camera_number, video_number)
        super().handle(file_name)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def send_multicast(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(bytes(message, 'utf-8'), (MCAST_GRP, MCAST_PORT))


def image(args):
    pic_time = time.time() + TRIGGER_DELAY
    send_multicast(TAKE_IMAGE_AT + str(pic_time))


def video(args):
    video_time = time.time() + TRIGGER_DELAY
    length = args.video_length if args.video_length else DEFAULT_VIDEO_LENGTH
    send_multicast(RECORD_VIDEO_FOR + str(length) + " at " + str(video_time))


def getimages(args):
    get_media(args, ImageTCPRequestHandler, SEND_LAST_IMAGE_TO)


def getvideos(args):
    get_media(args, VideoTCPRequestHandler, SEND_LAST_VIDEO_TO)


def get_media(args, request_handler, command):
    # start the receiver server
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "", 0
    number_of_cameras = args.cameras if args.cameras else DEFAULT_NUM_CAMERAS

    media_received_barrier = threading.Barrier(number_of_cameras + 1)

    class TCPRequestHandlerWithBarrier(request_handler):
        received_barrier = media_received_barrier

    server = ThreadedTCPServer((HOST, PORT), TCPRequestHandlerWithBarrier)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # tell each camera that they need to start sending me images
    ip, port = server.server_address
    send_multicast("{command}{ip}:{port}".format(
        command=command, ip=get_my_ip(), port=port))

    media_received_barrier.wait()
    server.shutdown()


def backlight_on(args):
    send_multicast(BACKLIGHT + "on")


def backlight_off(args):
    send_multicast(BACKLIGHT + "off")


def halt(args):
    send_multicast(HALT_AT + str(time.time() + TRIGGER_DELAY))


def reboot(args):
    send_multicast(REBOOT_AT + str(time.time() + TRIGGER_DELAY))


def get_my_ip():
    return run_cmd("hostname --all-ip-addresses")[:-1].strip()


def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command",
                        choices=['image', 'getimages', 'video', 'getvideos',
                                 'backlight-on', 'backlight-off',
                                 'halt', 'reboot'],
                        help="The command to run.")
    parser.add_argument('-c', '--cameras',
                        help="The number of cameras.",
                        type=int)
    parser.add_argument('-vl', '--video-length',
                        help="Length of video in miliseconds.",
                        type=int)
    args = parser.parse_args()

    commands = {
        'image': image,
        'getimages': getimages,
        'video': video,
        'getvideos': getvideos,
        'backlight-on': backlight_on,
        'backlight-off': backlight_off,
        'halt': halt,
        'reboot': reboot,
    }

    commands[args.command](args)
