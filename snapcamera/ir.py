from snapcamera.mode_option import ModeOption


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
