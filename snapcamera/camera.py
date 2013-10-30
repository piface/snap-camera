import os
import stat
import subprocess
import pifacecad
from pifacecad.lcd import LCD_WIDTH
from snapcamera.mode_option import (
    IMAGE_DIR,
    VIDEO_DIR,
    OVERLAY_DIR,
    CameraModeOption,
    VideoModeOption,
)
from snapcamera.effects import (
    CAMERA_EFFECTS,
    EffectsModeOption,
    OverlayModeOption,
)
from snapcamera.timelapse import (
    TimelapseModeOption,
)
from snapcamera.ir import (
    IRModeOption,
)
from snapcamera.viewer import (
    ViewerModeOption,
    image_index,
    video_index,
)
from snapcamera.network import (
    NetworkTriggerModeOption,
)


AVERAGE_IMAGE_SIZE = 2.4 * 1024 * 1024  # 2.4M is from `ls -l`
EGG_TIMER_BITMAP = pifacecad.LCDBitmap(
    [0x1f, 0x11, 0xa, 0x4, 0xa, 0x11, 0x1f, 0x0])  # no sand
    #[0x1f, 0x11, 0xa, 0x4, 0xa, 0x1d, 0x1f, 0x0])  # sand
EGG_TIMER_BITMAP_INDEX = 0


class Camera(object):
    """A camera for the Raspberry Pi which uses PiFace CAD and the RapspiCam.
    """
    def __init__(self, cad, start_mode='camera'):
        # make the image and overlay dirs
        for directory in (IMAGE_DIR, VIDEO_DIR, OVERLAY_DIR):
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                # rwx for everyone
                os.chmod(directory,
                         stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                         stat.S_IRGRP | stat.S_IWUSR | stat.S_IXGRP |
                         stat.S_IROTH | stat.S_IWUSR | stat.S_IXOTH)

        # this is a bit hacky
        #---------------------------------------------------------------
        # MAKE SURE YOU UPDATE THIS SECTION WHEN YOU CHANGE THE MODES
        possible_modes = ('camera', 'effects', 'overlay', 'timelapse', 'video',
                          'ir', 'network', 'viewer')
        self.current_mode_index = possible_modes.index(start_mode)

        self.modes = (
            {'name': 'camera', 'option': CameraModeOption(self)},
            {'name': 'effects', 'option': EffectsModeOption(self)},
            {'name': 'overlay', 'option': OverlayModeOption(self)},
            {'name': 'timelapse', 'option': TimelapseModeOption(self)},
            {'name': 'video', 'option': VideoModeOption(self)},
            {'name': 'IR', 'option': IRModeOption(self)},
            {'name': 'network', 'option': NetworkTriggerModeOption(self)},
            {'name': 'viewer', 'option': ViewerModeOption(self)},
        )
        #---------------------------------------------------------------
        self.cad = cad

        # camera options
        self.preview_on = True
        self.timeout = 0
        self.timelapse_interval = None
        self.effect = CAMERA_EFFECTS[0]

        self.cad.lcd.store_custom_bitmap(
            EGG_TIMER_BITMAP_INDEX, EGG_TIMER_BITMAP)

    @property
    def pictures_taken(self):
        return len(os.listdir(IMAGE_DIR))

    @property
    def pictures_remaining(self):
        return int(freespace(IMAGE_DIR) / AVERAGE_IMAGE_SIZE)

    @property
    def current_mode(self):
        return self.modes[self.current_mode_index]

    @property
    def last_image_number(self):
        images = filter(lambda filename: "image" in filename,
                        os.listdir(IMAGE_DIR))
        try:
            last_image = sorted(images)[-1]
        except IndexError:
            image_number = 0
        else:
            image_number = image_index(last_image)
            # last_image = last_image.strip(".jpgpng")
            # if '_' in last_image:
            #     last_image = last_image[:-5]  # get rid of the _0000
            # image_number = int(last_image[-4:])
        finally:
            return image_number

    @property
    def next_image_number(self):
        return self.last_image_number + 1

    @property
    def last_video_number(self):
        videos = filter(lambda filename: "video" in filename,
                        os.listdir(VIDEO_DIR))
        try:
            last_video = sorted(videos)[-1]
        except IndexError:
            video_number = 0
        else:
            video_number = video_index(last_video)
        finally:
            return video_number

    @property
    def next_video_number(self):
        return self.last_video_number + 1

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
            # removed timeout for normal images
            # timeout defaults to 5 with preview. Allows the camera to settle
            # command += ' --timeout {timeout} --output {filename}'.format(
            command += ' --output {filename}'.format(
                # timeout=self.timeout,
                filename=IMAGE_DIR+"image{:04}.jpg".format(
                    self.next_image_number),
            )
        command += " --nopreview" if not self.preview_on else ""
        command += " --imxfx {}".format(self.effect)
        command += ' --awb {}'.format('fluorescent')
        return command

    def build_video_command(self, length, filename=None):
        if filename is None:
            filename = "{video_dir}video{number:04}.h264".format(
                video_dir=VIDEO_DIR,
                number=self.next_video_number)
        command = 'raspivid'
        command += ' --timeout {timeout} --output {filename}'
        command += ' --exposure {exposure} --awb {awb}'
        command += ' --framerate {framerate}'
        # command += ' --width {width} --height {height}'
        # command += ' --bitrate {bitrate} --framerate {framerate}'
        command = command.format(
            timeout=length,
            filename=filename,
            exposure='fixedfps',
            awb='fluorescent',
            framerate=30,
            # width=1080,
            # height=720,
            # bitrate=10000000,  # 10 Mbps
            # framerate=24,
        )
        command += ' --nopreview' if not self.preview_on else ""
        return command

    def take_picture(self):
        """Captures a picture with the camera."""
        command = self.build_camera_command()
        self.run_camera_command(command)

    def record_video(self, length):
        """Captures video with the camera. Length is in miliseconds."""
        filename = "{video_dir}video{number:04}.h264".format(
            video_dir=VIDEO_DIR,
            number=self.next_video_number)
        self.run_camera_command(self.build_video_command(length, filename))
        self.convert_h264_to_mp4(filename)

    def convert_h264_to_mp4(self, h264filename):
        self.print_status_busy()
        command = "MP4Box -add {h264file} {mp4file}"
        command = command.format(h264file=h264filename,
                                 mp4file=h264filename.replace("h264", "mp4"))
        status = subprocess.call([command], shell=True)
        status |= self.remove_file(h264filename)
        if status == 0:
            self.print_status_not_busy()
        else:
            self.print_status_error()
        self.update_display_taken()
        self.update_display_remaining()

    def remove_file(self, filename):
        command = "rm {}".format(filename)
        status = subprocess.call([command], shell=True)
        return status

    def run_camera_command(self, command):
        self.print_status_busy()
        # print("KCH-CHSSHHH!")
        status = subprocess.call([command], shell=True)
        if status == 0:
            self.print_status_not_busy()
        else:
            self.print_status_error()
        self.update_display_taken()
        self.update_display_remaining()

    def print_status_busy(self):
        # self.print_status_char('#')
        self.cad.lcd.set_cursor(7, 0)
        self.cad.lcd.write_custom_bitmap(EGG_TIMER_BITMAP_INDEX)

    def print_status_not_busy(self):
        self.print_status_char(' ')

    def print_status_error(self):
        self.print_status_char('E')

    def print_status_char(self, character):
        # show that we're taking
        self.cad.lcd.set_cursor(7, 0)
        self.cad.lcd.write(character)

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
