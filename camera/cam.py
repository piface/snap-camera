import os
import subprocess
from pifacecad.lcd import LCD_WIDTH
from camera.mode_options import (
    CAMERA_EFFECTS,
    CameraModeOption,
    EffectsModeOption,
    TimelapseModeOption,
    IRModeOption,
    NetworkTriggerModeOption,
    ViewerModeOption,
)


IMAGE_DIR = "images/"
AVERAGE_IMAGE_SIZE = 2.4 * 1024 * 1024  # 2.4 is from `ls -l`


class Camera(object):
    """A camera for the Raspberry Pi which uses PiFace CAD and the RapspiCam.
    """
    def __init__(self, cad):
        self.current_mode_index = 0
        self.modes = (
            {'name': 'camera', 'option': CameraModeOption(self)},
            {'name': 'effects', 'option': EffectsModeOption(self)},
            {'name': 'timelapse', 'option': TimelapseModeOption(self)},
            {'name': 'IR', 'option': IRModeOption(self)},
            {'name': 'network', 'option': NetworkTriggerModeOption(self)},
            {'name': 'viewer', 'option': ViewerModeOption(self)},
        )
        self.cad = cad

        # camera options
        self.preview_on = False
        self.timeout = 0
        self.timelapse_interval = None
        self.effect = CAMERA_EFFECTS[0]

        # make the images dir
        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR)

    @property
    def pictures_taken(self):
        return len(os.listdir(IMAGE_DIR))

    @property
    def pictures_remaining(self):
        image_dir_full_path = "{}/../{}".format(
            os.path.dirname(os.path.realpath(__file__)), IMAGE_DIR)
        return int(freespace(image_dir_full_path) / AVERAGE_IMAGE_SIZE)

    @property
    def current_mode(self):
        return self.modes[self.current_mode_index]

    @property
    def next_image_number(self):
        try:
            last_image = sorted(os.listdir(IMAGE_DIR))[-1]
        except IndexError:
            last_image_number = 0
        else:
            last_image = last_image.strip(".jpgpng")
            if '_' in last_image:
                last_image = last_image[:-5]  # get rid of the _0000
            last_image_number = int(last_image[-4:])
        finally:
            return last_image_number + 1

    def build_camera_command(self):
        command = 'raspistill'
        if self.timelapse_interval is not None:
            command += ' --timeout {timelapse_period} '\
                ' --timelapse {timelapse_interval}'\
                ' --output {filename}'.format(
                    timelapse_period=self.timeout,
                    timelapse_interval=self.timelapse_interval,
                    filename=IMAGE_DIR+'image{:04}_%04d.jpg'.format(
                        self.next_image_number),
                )
        else:
            command += ' --timeout {timeout} --output {filename}'.format(
                timeout=self.timeout,
                filename=IMAGE_DIR+"image{:04}.jpg".format(
                    self.next_image_number),
            )
        command += " -n" if self.preview_on else ""
        command += " --imxfx {}".format(self.effect)
        return command

    def take_picture(self):
        """Captures a picture with the camera."""
        command = self.build_camera_command()
        print(command)

        # show that we're taking
        self.cad.lcd.set_cursor(7, 0)
        self.cad.lcd.write("#")

        print("KCH-CHSSHHH!")
        status = subprocess.call([command], shell=True)

        # show that we've finished
        self.cad.lcd.set_cursor(7, 0)
        self.cad.lcd.write(" " if status == 0 else "E")

        self.update_display_taken()
        self.update_display_remaining()

    def update_display(self):
        self.update_display_taken()
        self.update_display_remaining()
        self.update_display_mode()

    def update_display_taken(self):
        """Updates the taken section of the display."""
        width = 7
        taken_text = "t:{:04}".format(self.pictures_taken)
        taken_text = taken_text.ljust(width)[:width]
        self.cad.lcd.set_cursor(0, 0)
        self.cad.lcd.write(taken_text)

    def update_display_remaining(self):
        """Updates the remaining section of the display."""
        width = 8
        remaining_text = "r:{:04}".format(self.pictures_remaining)
        remaining_text = remaining_text.rjust(width)[:width]
        self.cad.lcd.set_cursor(LCD_WIDTH-width, 0)
        self.cad.lcd.write(remaining_text)

    def update_display_mode(self):
        """Updates the mode section of the display."""
        width = 8
        mode_name = self.current_mode['name']
        mode_name = mode_name.ljust(width)[:width]
        self.cad.lcd.set_cursor(0, 1)
        self.cad.lcd.write(mode_name)
        self.update_display_options()

    def update_display_options(self):
        """Updates the options section of the display."""
        self.current_mode['option'].update_display_option_text()


def freespace(path):
    """Returns the number of bytes available at the given path."""
    stats = os.statvfs(path)
    return stats.f_bsize * stats.f_bavail  # block size * blocks available
