#!/bin/bash
python setup.py --command-packages=stdeb.command sdist_dsc

version=$(cat snapcamera/version.py | sed 's/.*\([0-9]\.[0-9]\.[0-9]\).*/\1/')
cd deb_dist/snap-camera-$version/

cp {../../dpkg-files,debian}/control
cp {../../dpkg-files,debian}/copyright
cp {../../dpkg-files,debian}/rules
cp {../../dpkg-files,debian}/python3-snap-camera.install

mkdir debian/{bin,service}/
cp bin/snap-camera-service.sh debian/service/snap-camera
cp snap-camera.py debian/bin/snap-camera
cp snap-camera-network.py debian/bin/snap-camera-network

dpkg-buildpackage -us -uc
