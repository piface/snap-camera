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
        cad = pifacecad.PiFaceCAD(init_board=False)
        cad.lcd.display_off()
        cad.lcd.clear()
        cad.lcd.backlight_off()
    elif args.mode:
        #---------------------------------------------------------------
        # MAKE SURE YOU UPDATE snapcampera/camera.py WHEN YOU CHANGE THE MODES
        snapcamera.start_camera(args.mode)
        #---------------------------------------------------------------
    else:
        snapcamera.start_camera()
