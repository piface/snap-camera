#!/bin/bash
echo deb http://apt.piface.org.uk/ wheezy main >> /etc/apt/sources.list
apt-get update
# packages are unauthenticated and apt-get auto yes (-y) fails 
yes | apt-get install python3-pifacecommon python3-pifacedigitalio python3-pifacecad python3-pifacedigital-emulator python3-pifacedigital-scratch-handler python3-snap-camera
update-rc.d snap-camera defaults
reboot