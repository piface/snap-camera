#!/bin/bash
#: Description: Sets up bullet time on each RPi

# add the new source
echo deb http://apt.piface.org.uk/ wheezy main >> /etc/apt/sources.list &&
apt-get update &&

# packages are unauthenticated and apt-get auto yes (-y) fails
yes | apt-get install \
    python3-pifacecommon \
    python3-pifacedigitalio \
    python3-pifacecad \
    python3-pifacedigital-emulator \
    python3-pifacedigital-scratch-handler \
    python3-snap-camera &&

# alter the service to start the camera in network mode
echo "Updating the service script."
sed -e 's/\/usr\/bin\/python3 \/usr\/bin\/snap-camera \&/'\
    '\/usr\/bin\/python3 \/usr\/bin\/snap-camera --mode network \&/' \
    /etc/init.d/snap-camera > /tmp/snap-camera-service-new
cp /tmp/snap-camera-service-new /etc/init.d/snap-camera &&

# make the service run at boot
update-rc.d snap-camera defaults &&

reboot