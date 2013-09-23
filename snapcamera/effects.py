import os
from snapcamera.mode_option import ModeOption
from snapcamera.mode_option import (
    # IMAGE_DIR,
    OVERLAY_DIR,
)


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
        if self.current_overlay_index is not None:
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
        self.camera.print_status_busy()
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
        if status == 0:
            self.camera.print_status_not_busy()
        else:
            self.camera.print_status_error()

        self.update_display_option_text()

        # we have an extra image, update taken/remaining
        self.camera.update_display_taken()
        self.camera.update_display_remaining()
