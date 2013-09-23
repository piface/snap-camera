import threading
import socket
import struct
import socketserver
import subprocess
from snapcamera.mode_option import ModeOption


MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
SEND_LAST_IMAGE_TO = "send last image to "
TAKE_PICTURE_AT = "take picture at "
RECORD_VIDEO_AT = "record video at "
SHUTDOWN_AT = "shutdown at "
REBOOT_AT = "reboot at "
BACKLIGHT = "backlight "  # on/off
RUN_COMMNAD = "run command "


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
        self.number = 0

    def update_display_option_text(self):
        if self.server:
            super().update_display_option_text("#{}".format(self.number))
        else:
            super().update_display_option_text("error")

    def enter(self):
        # a bit of an ugly solution to pass handlers variables
        # http://stackoverflow.com/questions/12877185/
        #   pass-arguments-to-udp-handler-in-python
        class NetworkCommandHandlerWithCamera(NetworkCommandHandler):
            camera = self.camera

        try:
            self.server = ThreadedMulticastServer(
                ('', 0), NetworkCommandHandlerWithCamera)
        except socket.error as e:
            print(e)
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

    def next(self):
        if self.server:
            self.number += 1
            self.update_display_option_text()

    def previous(self):
        if self.server:
            self.number -= 1
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
            raise NetworkCommandHandlerError("I don't have a camera!")

        if TAKE_PICTURE_AT in data:
            picture_time = float(data[len(TAKE_PICTURE_AT):])
            self.take_picture_at(picture_time)
        elif SEND_LAST_IMAGE_TO in data:
            ip, port = data[len(SEND_LAST_IMAGE_TO):].split(":")
            last_image = sorted(os.listdir(IMAGE_DIR))[-1]
            self.send_image_to(ip, int(port), last_image)
        elif RECORD_VIDEO_AT in data:
            video_time = data[len(TAKE_PICTURE_AT):]
            self.record_video_at(video_time)
        elif SHUTDOWN_AT in data:
            shutdown_time = data[len(TAKE_PICTURE_AT):]
            self.shutdown_at(shutdown_time)
        elif REBOOT_AT in data:
            reboot_time = data[len(TAKE_PICTURE_AT):]
            self.reboot_at(reboot_time)
        elif BACKLIGHT in data:
            backlight_state = data[len(TAKE_PICTURE_AT):]
            self.set_backlight(backlight_state)
        elif RUN_COMMNAD in data:
            command = data[len(TAKE_PICTURE_AT):]
            self.run_command(command)

    def take_picture_at(self, picture_time):
        # wait until it's picture_time
        # while time.time() < picture_time:
        #     pass
        try:
            time.sleep(picture_time - time.time())
        except IOError:  # negative time
            pass
        finally:
            self.camera.take_picture()

    def send_image_to(self, ip, port, image_name):
        print("sending image to {}:{}".format(ip, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        camera_number = self.camera.current_mode['option'].number
        image_number = self.camera.last_image_number
        try:
            sock.send(bytes(str(camera_number).ljust(16), 'utf-8'))
            sock.send(bytes(str(image_number).ljust(16), 'utf-8'))
            with open(IMAGE_DIR + image_name, 'rb') as image:
                sock.sendall(image.read())
            # response = sock.recv(1024)
            # print "Received: {}".format(response)
        finally:
            sock.close()

    def record_video_at(self, video_time):
        pass

    def shutdown_at(self, shutdown_time):
        pass

    def reboot_at(self, reboot_time):
        pass

    def set_backlight(self, backlight_state):
        pass

    def run_command(self, command):
        pass


def get_my_ip():
    return run_cmd("hostname --all-ip-addresses")[:-1].strip()


def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')
