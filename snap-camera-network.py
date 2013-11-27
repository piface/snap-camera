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
        USING_CAMERAS,
        MCAST_GRP,
        MCAST_PORT,
        STREAM,
    )
except ImportError:
    # Fallback on the original command if the snapcamera module is not
    # installed.
    TAKE_IMAGE_AT = "take image at "
    SEND_LAST_IMAGE_TO = "send last image to "
    RECORD_VIDEO_FOR = "record video for "
    SEND_LAST_VIDEO_TO = "send last video to "
    HALT_AT = "halt at "
    REBOOT_AT = "reboot at "
    BACKLIGHT = "backlight "  # on/off
    RUN_COMMNAD = "run command "
    USING_CAMERAS = " using cameras "
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    STREAM = 'stream to '


TRIGGER_DELAY = 0.1  # seconds -- so that camera's can sync taking the photo
DEFAULT_NUM_CAMERAS = 1
DEFAULT_VIDEO_LENGTH = 5000  # milliseconds
PORT_OFFSET_DEFAULT = 13000


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
        print("Receiving from camera {}: image{}".format(camera_number,
                                                         image_number))
        file_name = "camera{:02}-image{:04}.jpg".format(camera_number,
                                                        image_number)
        super().handle(file_name)


class VideoTCPRequestHandler(TCPRequestHandler):
    def handle(self):
        camera_number = int(self.request.recv(16).decode('utf-8').strip())
        video_number = int(self.request.recv(16).decode('utf-8').strip())
        print("Receiving from camera {}: video{}".format(camera_number,
                                                         video_number))
        file_name = "camera{:02}-video{:04}.mp4".format(camera_number,
                                                        video_number)
        super().handle(file_name)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def send_multicast(message):
    #print(message)  # use this for debugging
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(bytes(message, 'utf-8'), (MCAST_GRP, MCAST_PORT))


def build_command(command, time=None, cameras=None):
    """Returns the command string.

    :param command: The command to run.
    :param time: The time to run the command.
    :param cameras: A list of camera numbers which should run the command.
    """
    cmd_str = command
    if time is not None:
        cmd_str += time
    if cameras is not None and len(cameras) > 0:
        cmd_str += USING_CAMERAS + ",".join(map(str, cameras))
    return cmd_str


def image(args, image_time=None):
    if image_time is None:
        image_time = time.time() + TRIGGER_DELAY
    send_multicast(build_command(TAKE_IMAGE_AT, str(image_time), args.cameras))


def video(args, video_time=None):
    if video_time is None:
        video_time = time.time() + TRIGGER_DELAY
    length = args.video_length if args.video_length else DEFAULT_VIDEO_LENGTH
    send_multicast(build_command(RECORD_VIDEO_FOR + str(length) + " at ",
                                 str(video_time),
                                 args.cameras))


def getimages(args):
    get_media(args, ImageTCPRequestHandler, SEND_LAST_IMAGE_TO)


def getvideos(args):
    get_media(args, VideoTCPRequestHandler, SEND_LAST_VIDEO_TO)


def get_media(args, request_handler, command):
    # start the receiver server
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "", 0
    if args.cameras[0]:
        number_of_cameras = args.cameras[0]
    else:
        DEFAULT_NUM_CAMERAS

    media_received_barrier = threading.Barrier(number_of_cameras + 1)

    class TCPRequestHandlerWithBarrier(request_handler):
        received_barrier = media_received_barrier

    server = ThreadedTCPServer((HOST, PORT), TCPRequestHandlerWithBarrier)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # tell each camera that they need to start sending me images
    ip, port = server.server_address
    cmd = "{command}{ip}:{port}".format(command=command,
                                        ip=get_my_ip(),
                                        port=port)
    send_multicast(build_command(cmd))

    media_received_barrier.wait()
    server.shutdown()


def backlight_on(args):
    send_multicast(build_command(BACKLIGHT + "on"))


def backlight_off(args):
    send_multicast(build_command(BACKLIGHT + "off"))


def halt(args):
    send_multicast(build_command(HALT_AT, str(time.time() + TRIGGER_DELAY)))


def reboot(args):
    send_multicast(build_command(REBOOT_AT, str(time.time() + TRIGGER_DELAY)))


def stream(args):
    steam_cmd = "{cmd} {ip} from port {port_offset}"
    steam_cmd = steam_cmd.format(cmd=STREAM,
                                 ip=get_my_ip(),
                                 port_offset=str(args.port_offset))
    send_multicast(steam_cmd)


def get_my_ip():
    return _run_cmd("hostname --all-ip-addresses")[:-1].strip()


def _run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command",
                        choices=['image', 'getimages', 'video', 'getvideos',
                                 'backlight-on', 'backlight-off',
                                 'halt', 'reboot',
                                 'stream'],
                        help="The command to run.")
    parser.add_argument('-c', '--cameras',
                        help="List of cameras to run the command on OR The "
                             "number of cameras expected to return media when "
                             "running getimages/getvideos.",
                        nargs='+',
                        type=int)
    parser.add_argument('-vl', '--video-length',
                        help="Length of video in miliseconds.",
                        type=int)
    parser.add_argument('-po', '--port-offset',
                        help="Number from which cameras offset their "
                             "streaming port. Streaming port = port offset + "
                             "camera number. (Default: {})".format(
                                 PORT_OFFSET_DEFAULT),
                        type=int,
                        default=PORT_OFFSET_DEFAULT)
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
        'stream': stream,
    }

    commands[args.command](args)
