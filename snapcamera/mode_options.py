import os
import re
import time
import struct
import socket
import threading
import multiprocessing
import subprocess
import socketserver
import pifacecad
from pifacecad.lcd import LCD_WIDTH


CAMERA_EFFECTS = (
    'none',
    'negative',
    'solarise',
    'posterize',
    'whiteboard',
    'blackboard',
    'sketch',
    'denoise',
    'emboss',
    'oilpaint',
    'hatch',
    'gpen',
    'pastel',
    'watercolour',
    'film',
    'blur',
    'saturation',
    'colourswap',
    'washedout',
    'posterise',
    'colourpoint',
    'colourbalance',
    'cartoon',
)

# IMAGE_DIR = "{}/../{}".format(
#     os.path.dirname(os.path.realpath(__file__)), "images/")
# OVERLAY_DIR = "{}/../{}".format(
#     os.path.dirname(os.path.realpath(__file__)), "overlay/")
IMAGE_DIR = "/home/pi/snap-camera/images/"
OVERLAY_DIR = "/home/pi/snap-camera/overlays/"

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
TAKE_PICTURE_AT = "take picture at "
SEND_LAST_IMAGE_TO = "send last image to "


class ModeOption(object):
    """A mode option. Subclass this and change the methods to define what
    happens when the user presses PiFaceCAD buttons.
    """
    def __init__(self, camera):
        self.camera = camera

    def pre_picture(self):
        """This function is called before the picture is taken."""
        pass

    def post_picture(self):
        """This function is called after the picture is taken."""
        pass

    def update_display_option_text(self, option_text=""):
        """This is what prints the option text."""
        width = 8
        self.camera.cad.lcd.set_cursor(LCD_WIDTH-width, 1)
        self.camera.cad.lcd.write(option_text.rjust(width)[:width])

    def update_camera(self):
        """Updates the camera state with the state of this mode."""
        pass

    def enter(self):
        """What to do when the mode is activated."""
        pass

    def exit(self):
        """What to do when the mode is deactivated (clean-up, usually)."""
        pass

    def next(self):
        """What to do when the next button is pressed and we are in this mode.
        """
        pass

    def previous(self):
        """What to do when the previous button is pressed and we are in this
        mode.
        """
        pass

    def option1(self):
        """What to do when the option 1 button is pressed."""
        pass

    def option2(self):
        """What to do when the option 2 button is pressed."""
        pass

    def option3(self):
        """What to do when the option 3 button is pressed."""
        pass


class CameraModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        # need to store this mode's delay state since another mode may change
        # the camera's timeout
        self.delay = 0

    def update_display_option_text(self):
        timeout_seconds = int(self.camera.timeout / 1000)
        super().update_display_option_text("dly {:02}".format(timeout_seconds))

    def update_camera(self):
        self.camera.timeout = self.delay

    def enter(self):
        self.update_camera()

    def next(self):
        self.delay += 1000
        self.update_camera()

    def previous(self):
        if self.delay > 0:
            self.delay -= 1000
            self.update_camera()


class EffectsModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        self.current_effect_index = 0
        self.effects = CAMERA_EFFECTS

    @property
    def current_effect(self):
        return self.effects[self.current_effect_index]

    @current_effect.setter
    def current_effect(self, effect_name):
        self.current_effect_index = self.effects.index(effect_name)

    def update_display_option_text(self):
        super().update_display_option_text(self.current_effect)

    def update_camera(self):
        self.camera.effect = self.current_effect

    def enter(self):
        self.update_camera()

    def exit(self):
        self.camera.effect = CAMERA_EFFECTS[0]

    def next(self):
        self.current_effect_index = \
            (self.current_effect_index + 1) % len(self.effects)
        self.update_camera()
        self.update_display_option_text()

    def previous(self):
        self.current_effect_index = \
            (self.current_effect_index - 1) % len(self.effects)
        self.update_camera()
        self.update_display_option_text()


class OverlayModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        self.current_overlay_index = 0 if len(self.overlays) > 0 else None

    @property
    def overlays(self):
        return sorted(os.listdir(OVERLAY_DIR))

    @property
    def current_overlay(self):
        if self.current_overlay_index:
            return self.overlays[self.current_overlay_index]
        else:
            return None

    @current_overlay.setter
    def current_overlay(self, effect_name):
        self.current_overlay_index = self.overlays.index(effect_name)

    def update_display_option_text(self):
        super().update_display_option_text(
            str(self.current_overlay).replace(".png", ""))

    def next(self):
        if not self.current_overlay:
            return
        self.current_overlay_index = \
            (self.current_overlay_index + 1) % len(self.overlays)
        self.update_camera()
        self.update_display_option_text()

    def previous(self):
        if not self.current_overlay:
            return
        self.current_overlay_index = \
            (self.current_overlay_index - 1) % len(self.overlays)
        self.update_camera()
        self.update_display_option_text()

    def post_picture(self):
        if not self.current_overlay:
            return

        # show that we're taking
        self.camera.print_status_char("#")
        super().update_display_option_text("working")

        original_image = "image{:04}.jpg".format(self.camera.last_image_number)

        new_image = "image{:04}-{}.jpg".format(
            self.camera.last_image_number,
            self.current_overlay.replace(".png", ""))

        command = "composite -geometry +500+500 -quality 100 "\
            "{overlay} {original_image} {new_image}".format(
                overlay=OVERLAY_DIR+self.current_overlay,
                original_image=IMAGE_DIR+original_image,
                new_image=IMAGE_DIR+new_image)
        status = subprocess.call([command], shell=True)

        # show that we've finished
        self.camera.print_status_char(" " if status == 0 else "E")
        self.update_display_option_text()

        # we have an extra image, update taken/remaining
        self.camera.update_display_taken()
        self.camera.update_display_remaining()


class ViewerModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        # current image index is the number in the image name
        try:
            # get the first image index
            self.current_image_index = image_index(self.images[0])
        except IndexError:
            self.current_image_index = 0

    @property
    def images(self):
        return sorted(os.listdir(IMAGE_DIR))

    def update_display_option_text(self):
        image_number = image_index(
            self.images[self.current_image_index])
        super().update_display_option_text(str(image_number))

    def enter(self):
        self.kill_image_viewer()
        self.start_image_viewer()

    def exit(self):
        self.kill_image_viewer()

    def next(self):
        self.kill_image_viewer()
        self.increment_image_index()
        self.update_display_option_text()
        self.start_image_viewer()

    def previous(self):
        self.kill_image_viewer()
        self.decrement_image_index()
        self.update_display_option_text()
        self.start_image_viewer()

    def kill_image_viewer(self):
        subprocess.call(['sudo killall fbi'], shell=True)

    def start_image_viewer(self):
        image_file = self.images[self.current_image_index]
        command = 'sudo fbi -autodown -T 1 {image}'.format(
            image=IMAGE_DIR + image_file)
        subprocess.call([command], shell=True)

    def increment_image_index(self):
        if len(self.images) == 0:
            return
        # elif self.current_image_index == 0:
        #     self.current_image_index = 1
        else:
            self.current_image_index = \
                (self.current_image_index + 1) % len(self.images)

    def decrement_image_index(self):
        if len(self.images) == 0:
            return
        # elif self.current_image_index == 0:
        #     self.current_image_index = 1
        else:
            self.current_image_index = \
                (self.current_image_index - 1) % len(self.images)


class TimelapseModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        self.period = 10000
        self.interval = 2000
        self.selected = 'period'

    def update_display_option_text(self):
        period_delay_seconds = int(self.camera.timeout / 1000)
        interval_delay_seconds = int(self.camera.timelapse_interval / 1000)
        if self.selected == 'interval':
            super().update_display_option_text("{}/[{}]".format(
                period_delay_seconds, interval_delay_seconds))
        else:
            super().update_display_option_text("[{}]/{}".format(
                period_delay_seconds, interval_delay_seconds))

    def update_camera(self):
        self.camera.timeout = self.period
        self.camera.timelapse_interval = self.interval

    def enter(self):
        self._old_camera_timeout = self.camera.timeout
        self.update_camera()

    def exit(self):
        self.camera.timelapse_interval = None
        self.camera.timeout = self._old_camera_timeout

    def next(self):
        if self.selected == 'period':
            self.period += 1000
        else:
            self.interval += 1000
        self.update_camera()
        self.update_display_option_text()

    def previous(self):
        if self.selected == 'period':
            if self.period >= 1000:
                self.period -= 1000
        else:
            if self.interval >= 1000:
                self.interval -= 1000
        self.update_camera()
        self.update_display_option_text()

    def option1(self):
        self.selected = 'interval' if self.selected == 'period' else 'period'
        self.update_display_option_text()


class IRModeOption(ModeOption):
    def enter(self):
        try:
            self.ir_listener = pifacecad.IREventListener('camera')
            self.ir_listener.register('0', self.take_picture)
            self.ir_listener.activate()
            self.ir_listener_is_active = True
            self.error = False
        except Exception as e:
            super().update_display_option_text("error")
            self.ir_listener_is_active = False
            self.error = True
            print("ERROR (IR Mode):", e)

    def update_display_option_text(self):
        message = "error" if self.error else ""
        super().update_display_option_text(message)

    def exit(self):
        if self.ir_listener_is_active:
            self.ir_listener.deactivate()

    def take_picture(self, event):
        self.camera.take_picture()
        # print("IR: taking picture.")
        # multiprocessing.Process(target=self.camera.take_picture).start()
        # print("IR: not my problem")


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
        except socket.error:
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

    def take_picture_at(self, picture_time):
        # wait until it's picture_time
        while time.time() < picture_time:
            pass
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


def get_my_ip():
    return run_cmd("hostname --all-ip-addresses")[:-1].strip()


def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


def image_index(image_string):
    """Returns the index of the image given. For example: image0010.jpg -> 10
    """
    #return int(image_string.replace("image", "").replace(".jpg", ""))
    return int(re.sub(r'image([0-9]{4}).*', r'\1', image_string))
