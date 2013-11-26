from snapcamera.mode_option import ModeOption


class TimelapseModeOption(ModeOption):
    def __init__(self, *args):
        super().__init__(*args)
        self.period = 1000
        self.interval = 1000
        self.selected = 'period'

        self.intervalIndex = 0
        self.periodIndex = 0
        self.timePrint = ["s","m","h"]
        self.timePrintCaps = ["S","M","H"]
        self.timeNumbers = [1000,60000,3600000]

    def update_display_option_text(self):
        period_delay_seconds = int(self.camera.timeout / self.timeNumbers[self.periodIndex])
        interval_delay_seconds = int(self.camera.timelapse_interval / self.timeNumbers[self.intervalIndex])
        if self.selected == 'interval':
            super().update_display_option_text("{}{}{}{}".format(self.timePrint[self.periodIndex],
                period_delay_seconds, self.timePrintCaps[self.intervalIndex],interval_delay_seconds))
        else:
            super().update_display_option_text("{}{}{}{}".format(self.timePrintCaps[self.periodIndex],
                period_delay_seconds, self.timePrint[self.intervalIndex], interval_delay_seconds))


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
            self.period += self.timeNumbers[self.periodIndex]
        else:
            self.interval += self.timeNumbers[self.intervalIndex]
        self.update_camera()
        self.update_display_option_text()

    def previous(self):
        if self.selected == 'period':
            if self.period >= self.timeNumbers[self.periodIndex]:
                self.period -= self.timeNumbers[self.periodIndex]
            else:
                self.period = 0
        else:
            if self.interval >= self.timeNumbers[self.intervalIndex]:
                self.interval -= self.timeNumbers[self.intervalIndex]
            else:
                self.interval = 0
        self.update_camera()
        self.update_display_option_text()

    def option1(self):
        # print("option 1 pressed")
        self.selected = 'interval' if self.selected == 'period' else 'period'
        self.update_display_option_text()

    def option2(self):
        # print("option 2 pressed")
        self.periodIndex = (self.periodIndex+1)%3
        self.period = self.timeNumbers[self.periodIndex]
        self.update_camera()
        self.update_display_option_text()

    def option3(self):
        # print("option 3 pressed")
        self.intervalIndex = (self.intervalIndex+1)%3
        self.interval = self.timeNumbers[self.intervalIndex]
        self.update_camera()
        self.update_display_option_text()
