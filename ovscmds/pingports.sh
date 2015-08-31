#!/bin/bash
SERVICES="192.168.1.111 192.168.1.110 192.168.1.200 192.168.1.201 192.168.1.202"

echo "################## START 192.168.1.111 #############################"
for i in $SERVICES
do
ping $i -c 3
done

echo "################## START 192.168.1.200 #############################"
for i in $SERVICES
do
ip netns exec ns0 ping $i -c 3
done
echo "################## START 192.168.1.201 #############################"
for i in $SERVICES
do
ip netns exec ns1 ping $i -c 3
done
echo "################## START 192.168.1.202 #############################"
for i in $SERVICES
do
ip netns exec ns2 ping $i -c 3
done
