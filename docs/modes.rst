#####
Modes
#####

The LCD is divided up into four segments: the number of taken images, the
number of remaining images, the mode and the mode option. Occasionally a
status symbol will also be shown in the center of the top line. Everything
is located as follows::

                    [5]
                  [6] [7]
      +----------------+
      |Taken     Remain|
      |Mode    Mode Op.|
      +----------------+
    [0] [1] [2] [3]   [4]

The button layout is:

====== ========================
Button Function
====== ========================
0      Change mode
1      Mode option button 1
2      Mode option button 2
3      Mode option button 3
4      Unused (exit in testing)
5      Take picture/video
6      Mode option previous
7      Mode option next
====== ========================

The status symbols are:

========= =========
Symbol    Meaning
========= =========
Egg timer Busy
!         Attention
E         Error
========= =========

While you can use button 0 to change the mode of the camera, it is sometimes
useful to be able to start the camera in a certain mode. You can do this with
the ``mode`` flag::

    $ snap-camera --mode effects


Camera
======
Camera mode is the default mode. Press the navigation switch in to take a
picture. Move the navigation switch left or right to change the delay
period. This is the amount of time the camera will wait before taking the
picture.

====== ==============
Button Function
====== ==============
0      Change mode
5      Take picture
6      Decrease delay
7      Increase delay
====== ==============


Effects
=======
Effects mode allows you to select an effect that will be applied to your
image. Move the navigation switch left or right to select an effect.

====== ===============
Button Function
====== ===============
0      Change mode
5      Take picture
6      Previous effect
7      Next effect
====== ===============


Overlay
=======
Overlay mode allows you to overlay an image stored at
``/home/pi/snap-camera/overlays`` on top of your image.

====== ================
Button Function
====== ================
0      Change mode
5      Take picture
6      Previous overlay
7      Next overlay
====== ================


Timelapse
=========
Timelapse mode will continually take images for a certain period at set
intervals. The period and interval can be seen in the `mode options` section.
The number and letter on the left is the total period. The number and
letter on the right is the interval length.

The currently selected mode option (period/interval) is denoted with a
capital letter. You can change which mode option you have selected with
`option 1` (button 1). You can change the units
(**s**\ econd/**m**\ inute/**h**\ our/**d**\ ay) of the period with option 2
(button 2) and of the interval with option 3 (button 3). You can change
the values of the period/interval by using the navigation switch.

====== ===============================================
Button Function
====== ===============================================
0      Change mode
1      Change selected mode option (period/interval)
2      Change units of period
3      Change units of interval
5      Take picture
6      Decrease selected mode option (period/interval)
7      Increase selected mode option (period/interval)
====== ===============================================

.. note:: Period / Interval = Number of pictures taken. Confirm this with
          the remaining pictures above. If too many pictures are to be
          taken the camera will flash the `attention` symbol before
          continuing with taking the images.


Video
=====
Record a video. Change the length of time with the navigation switch.

====== =====================
Button Function
====== =====================
0      Change mode
5      Start recording
6      Decrease video length
7      Increase video length
====== =====================


IR
==
Take a picture triggered by an IR remote. Press 1 on the remote to take
the image.

====== ============
Button Function
====== ============
0      Change mode
5      Take picture
====== ============

.. note:: You must have LIRC correctly configured with a remote for this
          mode to work.


Network
=======
You can control Snap Camera from the network. Use the navigation switch to
change the ID number of this camera (useful for when you have more that one
Snap Camera). Press option 1 to view the IP address of this camera. Press
it again to go back to viewing the camera number.

====== =======================
Button Function
====== =======================
0      Change mode
1      Toggle Camera Number/IP
5      Take picture
6      Increase camera number
7      Decrease camera number
====== =======================

.. note:: Network mode will error if not connected to a network.

While in network mode the camera can be controlled using the
``snap-camera-network`` program.


snap-camera-network
-------------------
Snap Camera Network can control the camera in several different ways. To
take an image with ``snap-camera-network`` run the following::

    $ snap-camera-network image

``snap-camera-network`` sends the command to all Snap Camera's on the
network.

Here is a list some more commands and what they do:

============= ==========================================================
Command       Function
============= ==========================================================
image         Takes a picture
getimages     Gets the last image from all cameras. You must specify
              how many cameras there are with the `-c` option becasue
              ``snap-camera-network`` needs to know how many images to
              wait for.
video         Starts recording a video. You must specify a length in
              milliseconds with the ``--video-length`` (``-vl``) option.
getvideos     Gets the last video from all cameras. You must specify
              how many cameras there are with the `-c` option becasue
              ``snap-camera-network`` needs to know how many videos to
              wait for.
backlight-on  Turns the backlight on.
backlight-off Turns the backlight off.
halt          Halts the Snap Camera (Raspberry Pi) .
reboot        Reboots the Snap Camera (Raspberry Pi).
stream        Streams video from Snap Camera. See below.
============= ==========================================================

Except for getimages and getvideos you can limit which Snap Cameras
accept commands by listing the camera numberss you want to respond using
the ``-c`` option. For example, if I only wanted cameras 1, 6 and 18 to
take an image, I would run::

    $ snap-camera-network image -c 1 6 18

For a help summary run::

    $ snap-camera-network --help

Streaming video
^^^^^^^^^^^^^^^
Snap Camera uses `netcat <http://netcat.sourceforge.net/>`_ to send a
video stream over the network. It sends the video on port
13000 + `Camera ID` (Snap Camera ID 3 will send it on port 13003).
Before requesting that Snap Camera begin streaming video you must first
prepare to accept the video stream and pipe it into something that will
play it. For this we will use `netcat` and `mplayer` like so::

    $ nc -l -p 13001 | mplayer -fps 31 -cache 1024 -

Notice how this is accepting a video stream from a Snap Camera with
network ID 1 becasue the port is 1300\ **1**.

After running this, mplayer will wait for a video stream to be recevied.
Now, in another terminal, tell Snap Camera to stream the video::

    $ snap-camera-network stream

In a few seconds you should see the video stream.


Viewer
======
Viewer mode allows you to view your images on a connected monitor. Move
the navigation switch left and right to change image.

====== ==============
Button Function
====== ==============
0      Change mode
5      Take picture
6      Previous image
7      Next image
====== ==============
