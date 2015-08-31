#!/bin/bash
SERVICES="0 1 2"
for i in $SERVICES
do
ovs-vsctl add-port ovsbr p$i -- set Interface p$i ofport_request=10$i
ovs-vsctl set Interface p$i type=internal
ip netns add ns$i
ip link set p$i netns ns$i
ip netns exec ns$i ip addr add 192.168.1.20$i/24 dev p$i
ip netns exec ns$i ifconfig p$i promisc up
sleep 1
done

clear
echo "##### OVS SHOW #####"
ovs-vsctl show
ovs-ofctl show ovsbr
echo "##### NETNS SHOW #####"
ip netns list
echo "##### IP Info #####"
for i in $SERVICES
do
ip netns exec ns$i ip a
done
