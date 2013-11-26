import os
import threading
import pifacecad
from pifacecad.lcd import LCD_WIDTH
from snapcamera.camera import Camera


def previous_mode(event):
    global camera
    camera.current_mode['option'].exit()
    camera.current_mode_index = \
        (camera.current_mode_index - 1) % len(camera.modes)
    camera.current_mode['option'].enter()
    camera.update_display_mode()


def next_mode(event):
    global camera
    camera.current_mode['option'].exit()
    camera.current_mode_index = \
        (camera.current_mode_index + 1) % len(camera.modes)
    camera.current_mode['option'].enter()
    camera.update_display_mode()


def previous_option(event):
    global camera
    camera.current_mode['option'].previous()
    camera.update_display_options()


def next_option(event):
    global camera
    camera.current_mode['option'].next()
    camera.update_display_options()


def option1(event):
    global camera
    camera.current_mode['option'].option1()


def option2(event):
    global camera
    camera.current_mode['option'].option2()


def option3(event):
    global camera
    camera.current_mode['option'].option3()


def take_picture(event):
    global camera

    # do the pre_picture, if it returns false, don't take the picture
    gogogo = camera.current_mode['option'].pre_picture()
    if gogogo is not None and gogogo is False:
        return

    if camera.current_mode['name'] == 'video':
        l = camera.current_mode['option'].length
        camera.record_video(l)
    else:
        camera.take_picture()
    camera.current_mode['option'].post_picture()


def exit(event):
    global should_i_exit
    should_i_exit.wait()


def start_camera(start_mode='camera'):
    cad = pifacecad.PiFaceCAD()

    switchlistener = pifacecad.SwitchEventListener(chip=cad)
    switchlistener.register(0, pifacecad.IODIR_ON, next_mode)
    switchlistener.register(1, pifacecad.IODIR_ON, option1)
    switchlistener.register(2, pifacecad.IODIR_ON, option2)
    switchlistener.register(3, pifacecad.IODIR_ON, option3)
    # switchlistener.register(4, pifacecad.IODIR_ON, exit)
    switchlistener.register(5, pifacecad.IODIR_ON, take_picture)
    switchlistener.register(6, pifacecad.IODIR_ON, previous_option)
    switchlistener.register(7, pifacecad.IODIR_ON, next_option)

    cad.lcd.display_off()
    cad.lcd.blink_off()
    cad.lcd.cursor_off()
    cad.lcd.clear()
    cad.lcd.backlight_on()
    global camera
    camera = Camera(cad, start_mode)
    camera.current_mode['option'].enter()
    camera.update_display()
    cad.lcd.display_on()

    global should_i_exit
    should_i_exit = threading.Barrier(2)
    switchlistener.activate()
    should_i_exit.wait()
    switchlistener.deactivate()
    cad.lcd.clear()
    cad.lcd.backlight_off()
    print("Good-bye!")
