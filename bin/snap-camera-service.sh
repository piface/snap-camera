### BEGIN INIT INFO
# Provides: camera
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Camera (PiFaceCAD + Raspicam) service.
# Description:       Camera (PiFaceCAD + Raspicam) service.
### END INIT INFO

LOCKFILE="/var/lock/snap_camera_service.lock"

start() {
        echo -n "Starting snap-camera service: "
        /usr/bin/python3 /usr/bin/snap-camera --mode network &
        ### Create the lock file ###
        echo $! > $LOCKFILE
        status
}

stop() {
        echo -n "Stopping snap-camera service: "
        pid=$(cat $LOCKFILE)
        kill $pid
        # Now, delete the lock file ###
        rm -f $LOCKFILE
        # clean up the screen
        /usr/bin/python3 /usr/bin/snap-camera --clear
        status
}

status() {
        if [ -e $LOCKFILE ]
        then
            echo "[Running]"
        else
            echo "[Stopped]"
        fi
}

### main logic ###
case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  status)
        status
        ;;
  restart|reload|force-reload)
        stop
        start
        ;;
  *)
        echo $"Usage: $0 {start|stop|restart|reload|force-reload|status}"
        exit 1
esac
exit 0
