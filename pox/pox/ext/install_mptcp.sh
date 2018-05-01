#
# Installs MPTCP in the system.
#
#   From: https://multipath-tcp.org/pmwiki.php/Users/AptRepository
#

# Install the MPTCP implementation
sudo apt-key adv --keyserver hkp://keys.gnupg.net --recv-keys 379CE192D401AB61
sudo sh -c "echo 'deb https://dl.bintray.com/cpaasch/deb stretch main' > /etc/apt/sources.list.d/mptcp.list"
sudo apt-get update
sudo apt-get install linux-mptcp

# Some configuration steps
sudo cp mptcp_up /etc/network/if-up.d/
sudo chmod +x /etc/network/if-up.d/mptcp_up

sudo cp mptcp_down /etc/network/if-post-down.d/
sudo chmod +x /etc/network/if-post-down.d/mptcp_down

# Restart networking
sudo service network-manager restart

echo 'You need to reboot your machine.  Then run `uname -a` to double check you see an MPTCP kernel'