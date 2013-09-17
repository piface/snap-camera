#!/usr/bin/python3
import snapcamera
import argparse
import pifacecad


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--clear', help='Clears the LCD.', action='store_true')
    parser.add_argument('--mode', help='Mode to start in.', choices=[
        'camera',
        'effects',
        'overlay',
        'timelapse',
        'ir',
        'network',
        'viewer'])
    args = parser.parse_args()
    if args.clear:
        pifacecad.init()
        pifacecad.PiFaceCAD().lcd.display_off()
        pifacecad.PiFaceCAD().lcd.clear()
        pifacecad.PiFaceCAD().lcd.backlight_off()
        pifacecad.deinit()
    elif args.mode:
        #---------------------------------------------------------------
        # MAKE SURE YOU UPDATE snapcampera/camera.py WHEN YOU CHANGE THE MODES
        snapcamera.start_camera(args.mode)
        #---------------------------------------------------------------
    else:
        snapcamera.start_camera()
