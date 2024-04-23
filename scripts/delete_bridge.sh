#!/bin/bash
#本脚本删除的是br-开头的网桥
BRIDGE_LIST=$(sudo brctl show | cut -f 1 | grep br)
echo "即将删除的网桥是："$BRIDGE_LIST
for i in $BRIDGE_LIST
do
    sudo ifconfig $i down
    sudo brctl delbr $i
done
echo "删除之后用主机网桥状态如下："
echo sudo brctl show
