import threading
import socket
import struct
import socketserver
import subprocess
import time
import sched
import os
from snapcamera.mode_option import (
    IMAGE_DIR,
    VIDEO_DIR,
    ModeOption,
)


MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
SEND_LAST_IMAGE_TO = "send last image to "
SEND_LAST_VIDEO_TO = "send last video to "
TAKE_IMAGE_AT = "take image at "
RECORD_VIDEO_FOR = "record video for "  # <length> at <time>
HALT_AT = "halt at "
REBOOT_AT = "reboot at "
BACKLIGHT = "backlight "  # on/off
RUN_COMMNAD = "run command "
USING_CAMERAS = " using cameras "

CAM_NUM_FILE = "camera-number.txt"

TRY_AGAIN_ATTEMPTS = 6
TRY_AGAIN_TIME = 10  # seconds


class ThreadedMulticastServer(
        socketserver.ThreadingMixIn, socketserver.UDPServer):
    """Voodoo.
    http://stackoverflow.com/questions/12357435/
        python-socketserver-listen-on-multicast
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((MCAST_GRP, MCAST_PORT))
        mreq = struct.pack(
            "4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.socket.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        # SOCKET SOCKET SOCKET!


class NetworkTriggerModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        self.server = None
        self.try_again_timer = None
        self.server_start_attempts = 0
        self.display_mode = 'number'

        # check for camera number
        try:
            f = open(CAM_NUM_FILE, 'r')
        except IOError:
            self.number = 0
            self.save_number_to_file()
        else:
            self.load_number_from_file()

    def load_number_from_file(self):
        with open(CAM_NUM_FILE, 'r') as num_file:
            self.number = int(num_file.read())

    def save_number_to_file(self):
        with open(CAM_NUM_FILE, 'w') as num_file:
            num_file.write(str(self.number))

    def update_display_option_text(self):
        if self.server:
            if self.display_mode == 'number':
                super().update_display_option_text("#{}".format(self.number))
            elif self.display_mode == 'ip':
                subnet, end = get_my_ip().split(".")[-2:]
                ipstr = ".{}.{}".format(subnet, end)
                super().update_display_option_text(ipstr)
        elif self.server_start_attempts < TRY_AGAIN_ATTEMPTS:
            super().update_display_option_text("wait")
        else:
            super().update_display_option_text("error")

    def enter(self):
        # a bit of an ugly solution to pass handlers variables
        # http://stackoverflow.com/questions/12877185/
        #   pass-arguments-to-udp-handler-in-python
        class NetworkCommandHandlerWithCamera(NetworkCommandHandler):
            camera = self.camera

        self.server_start_attempts += 1
        try:
            self.server = ThreadedMulticastServer(
                ('', 0), NetworkCommandHandlerWithCamera)
        except socket.error as e:
            print(e)
            if self.server_start_attempts < TRY_AGAIN_ATTEMPTS:
                print("Trying again in {} seconds.".format(TRY_AGAIN_TIME))
                self.try_again_timer = threading.Timer(TRY_AGAIN_TIME,
                                                       self.enter)
                self.try_again_timer.start()
            self.update_display_option_text()
            return

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        print("Started multicast server {}:{}.".format(MCAST_GRP, MCAST_PORT))
        self.update_display_option_text()

    def exit(self):
        if self.server:
            self.server.shutdown()
            print("Stopped server.")
        if self.try_again_timer:
            self.try_again_timer.cancel()

    def next(self):
        if self.server:
            self.number += 1
            self.update_display_option_text()
            self.save_number_to_file()

    def previous(self):
        if self.server:
            self.number -= 1
            self.update_display_option_text()
            self.save_number_to_file()

    def option1(self):
        """Changes the display mode."""
        if self.display_mode == 'number':
            self.display_mode = 'ip'
        else:
            self.display_mode = 'number'
        self.update_display_option_text()


class NetworkCommandHandlerError(Exception):
    pass


class NetworkCommandHandler(socketserver.BaseRequestHandler):
    camera = None

    def handle(self):
        data = str(self.request[0], 'utf-8')
        socket = self.request[1]
        print("Received ({}):".format(time.time()), data)

        if self.camera is None:
            # You need to subclass this before passing it to your server:
            # class NetworkCommandHandlerWithCamera(NetworkCommandHandler):
            #     camera = a_camera_object
            raise NetworkCommandHandlerError("I don't have a camera object!")

        if USING_CAMERAS in data:
            i = data.index(USING_CAMERAS) + len(USING_CAMERAS)
            cameras = data[i:].split(",")
            cameras = list(map(int, cameras))
            # only run the command if this camera is in the list of cameras
            if self.camera.current_mode['option'].number not in cameras:
                return
            else:
                i = data.index(USING_CAMERAS)
                data = data[:i]

        if TAKE_IMAGE_AT in data:
            picture_time = float(data[len(TAKE_IMAGE_AT):])
            self.take_picture_at(picture_time)

        elif RECORD_VIDEO_FOR in data:
            video_length, video_time = \
                data[len(RECORD_VIDEO_FOR):].split(" at ")
            self.record_video_at(int(video_length), float(video_time))

        elif SEND_LAST_IMAGE_TO in data:
            ip, port = data[len(SEND_LAST_IMAGE_TO):].split(":")
            last_image = sorted(os.listdir(IMAGE_DIR))[-1]
            self.send_image_to(ip, int(port), last_image)

        elif SEND_LAST_VIDEO_TO in data:
            ip, port = data[len(SEND_LAST_VIDEO_TO):].split(":")
            last_video = sorted(os.listdir(VIDEO_DIR))[-1]
            self.send_video_to(ip, int(port), last_video)

        elif HALT_AT in data:
            halt_time = float(data[len(HALT_AT):])
            self.halt_at(halt_time)

        elif REBOOT_AT in data:
            reboot_time = float(data[len(REBOOT_AT):])
            self.reboot_at(reboot_time)

        elif BACKLIGHT in data:
            backlight_state = data[len(BACKLIGHT):]
            self.set_backlight(backlight_state == "on")

        elif RUN_COMMNAD in data:
            command = data[len(RUN_COMMNAD):]
            self.run_command(command)

    def take_picture_at(self, picture_time):
        s = sched.scheduler(time.time, time.sleep)
        s.enterabs(picture_time, 1, self.camera.take_picture, tuple())
        s.run()

    def record_video_at(self, video_length, video_time):
        s = sched.scheduler(time.time, time.sleep)
        s.enterabs(video_time, 1, self.camera.record_video, (video_length,))
        s.run()

    def send_image_to(self, ip, port, image_name):
        print("sending image to {}:{}".format(ip, port))
        image_number = self.camera.last_image_number
        self.send_media_to(ip, port, image_name, image_number, IMAGE_DIR)

    def send_video_to(self, ip, port, video_name):
        print("sending video to {}:{}".format(ip, port))
        video_number = self.camera.last_video_number
        self.send_media_to(ip, port, video_name, video_number, VIDEO_DIR)

    def send_media_to(self, ip, port, media_name, media_number, media_dir):
        camera_number = self.camera.current_mode['option'].number
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        try:
            sock.send(bytes(str(camera_number).ljust(16), 'utf-8'))
            sock.send(bytes(str(media_number).ljust(16), 'utf-8'))
            with open(media_dir + media_name, 'rb') as media:
                sock.sendall(media.read())
        finally:
            sock.close()

    def halt_at(self, halt_time):
        s = sched.scheduler(time.time, time.sleep)
        s.enterabs(halt_time, 1, self.halt, tuple())
        s.run()

    def reboot_at(self, reboot_time):
        s = sched.scheduler(time.time, time.sleep)
        s.enterabs(reboot_time, 1, self.reboot, tuple())
        s.run()

    def halt(self):
        self.camera.cad.lcd.clear()
        self.camera.cad.lcd.write("Going down for\nsystem halt.")
        subprocess.call(['sudo', 'halt'])

    def reboot(self):
        self.camera.cad.lcd.clear()
        self.camera.cad.lcd.write("The system will\nreboot.")
        subprocess.call(['sudo', 'reboot'])

    def set_backlight(self, backlight_state):
        if backlight_state:
            self.camera.cad.lcd.backlight_on()
        else:
            self.camera.cad.lcd.backlight_off()

    def run_command(self, command):
        s = sched.scheduler(time.time, time.sleep)
        s.enterabs(start_time, 1, subprocess.call, (command.split(" ")))
        s.run()


def get_my_ip():
    return run_cmd("hostname --all-ip-addresses")[:-1].strip()


def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')
