sudo ip link add vbridge type bridge
sudo ip link set dev vbridge up
sudo ip netns add ns1
sudo ip netns add ns2
sudo ip link add veth-1 type veth peer name veth-1-br
sudo ip link add veth-2 type veth peer name veth-2-br
sudo ip link set veth-1 netns ns1
sudo ip link set veth-1-br master vbridge
sudo ip link set veth-2 netns ns2
sudo ip link set veth-2-br master vbridge
sudo ip netns exec ns1 ip addr add 192.168.28.1/24 dev veth-1
sudo ip netns exec ns2 ip addr add 192.168.28.2/24 dev veth-2
sudo ip netns exec ns1 ip link set veth-1 up
sudo ip link set dev veth-1-br up
sudo ip netns exec ns2 ip link set veth-2 up
sudo ip link set dev veth-2-br up