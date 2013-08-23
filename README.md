Camera
======
A camera that uses PiFace Control and Display and Raspicam.

Images are stored at `/home/pi/snap-camera/images/`.
Overlays are stored at `/home/pi/snap-camera/overlays/`.


Install
=======
Enable the camera with:

    raspi-config

Enable HDMI to start even when unplugged by uncommenting:

    hdmi_force_hotplug=1

in `/boot/config.txt`.

Download the latest debian package and install with:

    sudo dpkg -i python3-snap-camera_0.0.0-1_all.deb

Start/stop the camera service with:

    sudo service snap-camera start
    sudo service snap-camera stop

Enable the service at boot:

    sudo update-rc.d snap-camera enable

The camera should start up on boot.
