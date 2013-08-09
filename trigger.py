import time
import socket
try:
    from camera.mode_options import (
        TAKE_PICTURE_AT,
        MCAST_GRP,
        MCAST_PORT,
    )
except ImportError:
    # fallback on the original command if this script is not next to camera
    TAKE_PICTURE_AT = "take picture at "
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007


DELAY = 0.1  # seconds -- so that camera's can sync taking the photo


def send_multicast(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(bytes(message, 'utf-8'), (MCAST_GRP, MCAST_PORT))


if __name__ == "__main__":
    pic_time = time.time() + DELAY
    send_multicast(TAKE_PICTURE_AT + str(pic_time))
