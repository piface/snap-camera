import re
import os
import subprocess
from snapcamera.mode_option import ModeOption
from snapcamera.mode_option import (
    IMAGE_DIR,
    # OVERLAY_DIR,
)


class ViewerModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        # current image index is the number in the image name
        # try:
        #     # get the first image index
        #     self.current_image_index = image_index(self.images[0])
        # except IndexError:
        #     self.current_image_index = None
        self.current_image_index = 0 if len(self.images) > 0 else None

    @property
    def images(self):
        return sorted(os.listdir(IMAGE_DIR))

    @property
    def current_image(self):
        if self.current_image_index is not None:
            return self.images[self.current_image_index]
        else:
            return None

    def post_picture(self):
        # view latest image
        # if len(self.images) > 0:
        #     self.current_image_index = len(self.images) - 1

        # view first image
        if len(self.images) == 1:
            self.current_image_index = 0
            self.update_display_option_text()
            self.start_image_viewer()

    def update_display_option_text(self):
        if self.current_image is not None:
            image_number = image_index(self.current_image)
        else:
            image_number = None
        super().update_display_option_text(str(image_number))

    def enter(self):
        if len(self.images) > 0:
            self.current_image_index = len(self.images) - 1

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
        if self.current_image is None:
            return

        image_file = self.current_image
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


def image_index(image_string):
    """Returns the index of the image given. For example: image0010.jpg -> 10
    """
    #return int(image_string.replace("image", "").replace(".jpg", ""))
    return int(re.sub(r'image([0-9]{4}).*', r'\1', image_string))


def video_index(video_string):
    """Returns the index of the video given. For example: video0010.jpg -> 10
    """
    #return int(video_string.replace("video", "").replace(".jpg", ""))
    return int(re.sub(r'video([0-9]{4}).*', r'\1', video_string))
