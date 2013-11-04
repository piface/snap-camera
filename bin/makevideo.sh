#: Description: Creates a video from *.jpg in the current directory

SIZE=800x800
TMP_DIR="temp"
OUTPUT="output.mp4"
FPS=50

# Create a directory and copy the original images there for manipulation:
mkdir $TMP_DIR
cp *.jpg $TMP_DIR/.

# Resize the images:
echo "Resizing images."
mogrify -resize $SIZE  $TMP_DIR/*.jpg

# Create the morph images
echo "Morphing images for a smooth transition."
convert $TMP_DIR/*.jpg -delay 10 -morph 10 $TMP_DIR/%05d.jpg

# Stitch them together into a video
ffmpeg -r $FPS -qscale 2  -i $TMP_DIR/%05d.jpg $OUTPUT

# remove the temp directory
rm -r $TMP_DIR
