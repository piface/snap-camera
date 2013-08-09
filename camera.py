import camera
import argparse
import pifacecad


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--clear', help='Clears the LCD.', action='store_true')
    args = parser.parse_args()
    if args.clear:
        pifacecad.init()
        pifacecad.PiFaceCAD().lcd.clear()
        pifacecad.PiFaceCAD().lcd.backlight_off()
        pifacecad.PiFaceCAD().lcd.display_off()
        pifacecad.deinit()
    else:
        camera.start_camera()
