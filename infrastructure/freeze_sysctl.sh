# Script to freeze Kernel and Sysctl parameters
CONFIG_FILE="/etc/sysctl.d/99-cs525-graypulse.conf"

cat <<EOF > $CONFIG_FILE
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
vm.swappiness = 10
kernel.pid_max = 655360
EOF

sysctl -p $CONFIG_FILE
echo "System parameters have been frozen and applied via $CONFIG_FILE."
