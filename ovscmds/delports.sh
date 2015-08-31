#!/bin/bash
SERVICES="0 1 2"
for i in $SERVICES
do
ovs-vsctl del-port ovsbr p$i
ip netns delete ns$i
done

clear
echo "#####OVS SHOW#####"
ovs-vsctl show
ovs-ofctl show ovsbr
echo "#####NETNS SHOW#####"
ip netns list
