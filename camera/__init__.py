import os
import threading
import pifacecad
from pifacecad.lcd import LCD_WIDTH
from camera.cam import Camera


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
    camera.take_picture()


def exit(event):
    global should_i_exit
    should_i_exit.wait()


def start_camera():
    pifacecad.init()

    switchlistener = pifacecad.SwitchEventListener()
    switchlistener.register(0, pifacecad.IODIR_ON, next_mode)
    switchlistener.register(1, pifacecad.IODIR_ON, option1)
    switchlistener.register(2, pifacecad.IODIR_ON, option2)
    switchlistener.register(3, pifacecad.IODIR_ON, option3)
    # switchlistener.register(4, pifacecad.IODIR_ON, exit)
    switchlistener.register(5, pifacecad.IODIR_ON, take_picture)
    switchlistener.register(6, pifacecad.IODIR_ON, previous_option)
    switchlistener.register(7, pifacecad.IODIR_ON, next_option)

    cad = pifacecad.PiFaceCAD()
    cad.lcd.clear()
    cad.lcd.backlight_on()
    cad.lcd.blink_off()
    cad.lcd.cursor_off()
    global camera
    camera = Camera(cad)
    camera.update_display()

    global should_i_exit
    should_i_exit = threading.Barrier(2)
    switchlistener.activate()
    should_i_exit.wait()
    switchlistener.deactivate()
    cad.lcd.clear()
    cad.lcd.backlight_off()
    pifacecad.deinit()
    print("Good-bye!")
