from snapcamera.mode_option import ModeOption


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
