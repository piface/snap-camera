Camera
======
A camera that uses PiFace Control and Display and Raspicam.

Put this directory at `/home/pi/camera/`. Images are stored at
`/home/pi/camera/images/`.

Copy camera-service.sh to the daemons directory.

    cp camera-service.sh /etc/init.d/camera

Enable the service:

    sudo update-rc.d camera enable

The camera should start up on boot.


Enabling HDMI on boot even when unplugged (required for viewer)
---------------------------------------------------------------
Uncomment:

    hdmi_force_hotplug=1

in /boot/config.txt