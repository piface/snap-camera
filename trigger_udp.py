import time
import socket
import argparse
try:
    from camera.mode_options import TAKE_PICTURE_AT
except ImportError:
    # fallback on the original command if this script is not next to camera
    TAKE_PICTURE_AT = "take picture at "


DELAY = 0.1  # seconds -- increase to improve camera sync
DEFAULT_PORT = 55443


def send_udp(message, ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(message, 'utf-8'), (ip, port))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sockets",
        help="The sockets to send the UDP packet to. For example: "
             "192.168.0.10:{port} 192.168.0.11:{port}"
             .format(port=DEFAULT_PORT),
        nargs='*')
    args = parser.parse_args()

    pic_time = time.time() + DELAY
    for s in args.sockets:
        try:
            ip, port = s.split(":")
        except ValueError:
            ip, port = s, DEFAULT_PORT  # tolerant of not giving port
        finally:
            send_udp(TAKE_PICTURE_AT + str(pic_time), ip, int(port))
