#!/bin/bash
rm -r tmpcamera
mkdir tmpcamera
cd tmpcamera/
echo "Press ENTER to take cool picture!"
read
python3 ../snap-camera-network.py image

echo "Waiting for images to take..."
echo "Press enter to pull the images when ready."
read
python3 ../snap-camera-network.py getimages -c 23

echo "Making the cool pictures."
../bin/makevideo.sh
