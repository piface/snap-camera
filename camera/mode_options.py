import time
import struct
import socket
import threading
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

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
TAKE_PICTURE_AT = "take picture at "


class ModeOption(object):
    """A mode option. Subclass this and change the methods to define what
    happens when the user presses PiFaceCAD buttons.
    """
    def __init__(self, camera):
        self.camera = camera

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


class ViewerModeOption(ModeOption):
    pass


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
        self.ir_listener = pifacecad.IREventListener('camera')
        self.ir_listener.register('0', self.take_picture)
        self.ir_listener.activate()

    def exit(self):
        self.ir_listener.deactivate()

    def take_picture(self, event):
        self.camera.take_picture()


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
        self.show_port = True

    def update_display_option_text(self):
        # option_text = ""
        # if self.server:
        #     server_ip, port = self.server.server_address
        #     # get the last two ip segments
        #     ip = ".".join(get_my_ip().split(".")[-2:])
        #     option_text = str(port) if self.show_port else str(ip)

        option_text = "mcast"
        super().update_display_option_text(option_text)

    def enter(self):
        # a bit of an ugly solution to pass handlers variables
        # http://stackoverflow.com/questions/12877185/
        #   pass-arguments-to-udp-handler-in-python
        class NetworkCommandHandlerWithCamera(NetworkCommandHandler):
            camera = self.camera

        self.server = ThreadedMulticastServer(
            ('', 0), NetworkCommandHandlerWithCamera)

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        print("Started multicast server {}:{}.".format(MCAST_GRP, MCAST_PORT))
        self.update_display_option_text()

    def exit(self):
        self.server.shutdown()
        print("Stopped server.")

    def next(self):
        self.show_port = not self.show_port
        self.update_display_option_text()

    def previous(self):
        self.show_port = not self.show_port
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
            # wait until it's picture_time
            while time.time() < picture_time:
                pass
            self.camera.take_picture()


def get_my_ip():
    return run_cmd("hostname --all-ip-addresses")[:-1].strip()


def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')
