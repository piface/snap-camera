#!/bin/bash
#: Description: Setups up the DHCP server on the snap-camera master RPi

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# install the dhcp server
apt-get -y install isc-dhcp-server

# configure the dhcp server
# interface
#dpkg-reconfigure isc-dhcp-server  # interactive
cat > /etc/default/isc-dhcp-server << EOF
# Defaults for isc-dhcp-server initscript
# sourced by /etc/init.d/isc-dhcp-server
# installed at /etc/default/isc-dhcp-server by the maintainer scripts

#
# This is a POSIX shell fragment
#

# Path to dhcpd's config file (default: /etc/dhcp/dhcpd.conf).
#DHCPD_CONF=/etc/dhcp/dhcpd.conf

# Path to dhcpd's PID file (default: /var/run/dhcpd.pid).
#DHCPD_PID=/var/run/dhcpd.pid

# Additional options to start dhcpd with.
#       Don't use options -cf or -pf here; use DHCPD_CONF/ DHCPD_PID instead
#OPTIONS=""

# On what interfaces should the DHCP server (dhcpd) serve DHCP requests?
#       Separate multiple interfaces with spaces, e.g. "eth0 eth1".
INTERFACES="eth0"
EOF

# config file
cat > /etc/dhcp/dhcpd.conf << EOF
option domain-name "snap-camera-bullet-time";
#option domain-name-servers 8.8.8.8, 8.8.4.4;
# Set up our desired subnet:
# using 192.168.2 subnet so it is clear we are on snap-camera network
subnet 192.168.2.0 netmask 255.255.255.0 {
    range 192.168.2.100 192.168.2.254;
    option subnet-mask 255.255.255.0;
    option broadcast-address 192.168.2.255;
    option routers 192.168.2.100;
}
default-lease-time 600;
max-lease-time 7200;
# Show that we want to be the only DHCP server in this network:
authoritative;
EOF

# restart the dhcp server
/etc/init.d/isc-dhcp-server restart
