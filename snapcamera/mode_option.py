# should probably split this file up at some point...
import os
import re
import time
import struct
import socket
import threading
import subprocess
import pifacecad
from pifacecad.lcd import LCD_WIDTH


# IMAGE_DIR = "{}/../{}".format(
#     os.path.dirname(os.path.realpath(__file__)), "images/")
# OVERLAY_DIR = "{}/../{}".format(
#     os.path.dirname(os.path.realpath(__file__)), "overlay/")
IMAGE_DIR = "/home/pi/snap-camera/images/"
VIDEO_DIR = "/home/pi/snap-camera/videos/"
OVERLAY_DIR = "/home/pi/snap-camera/overlays/"


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


class VideoModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        self.length = 5000

    def update_display_option_text(self):
        timeout_seconds = int(self.camera.timeout / 1000)
        super().update_display_option_text(
            "len {:02}".format(timeout_seconds))

    def update_camera(self):
        self.camera.timeout = self.length

    def enter(self):
        self.update_camera()

    def next(self):
        self.length += 1000
        self.update_camera()

    def previous(self):
        if self.length > 0:
            self.length -= 1000
            self.update_camera()
