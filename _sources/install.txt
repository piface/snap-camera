############
Installation
############

Snap Camera is in the main Raspian Repositories. **Install** it with::

    $ sudo apt-get install python3-snap-camera

You must also enable the camera with::

    $ sudo raspi-config

And also uncomment ``hdmi_force_hotplug=1`` in ``/boot/config.txt``.

You start Snap Camera by running::

    $ snap-camera

Service
=======
Snap Camera also runs as a service. To **start** Snap Camera::

    $ sudo service snap-camera start

To **stop** Snap Camera::

    $ sudo service snap-camera stop

To enable Snap Camera to **run at boot**::

    $ sudo update-rc.d snap-camera defaults
