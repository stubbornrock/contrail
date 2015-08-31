import subprocess
print "=========>>> ADD NETWORK NAMESPACE INTERFACE TO OVS ... ..."

vm_name = 'test3'
ns_name = vm_name + 'ns'
vmi_name = 'veth1'
peth = vm_name + '-peth1'
mac = '02:88:d5:f8:63:b5'
ipaddr = '192.168.2.250'

subprocess.call('ip link add %s type veth peer name %s' %(vmi_name,peth), shell = True)
subprocess.call('ip link set %s netns %s' %(vmi_name,ns_name) , shell = True)
subprocess.call('ip netns exec %s ip link set dev %s address %s' %(ns_name,vmi_name,mac), shell = True)
subprocess.call('ip netns exec %s ip addr add %s dev %s' %(ns_name,ipaddr,vmi_name), shell = True)
subprocess.call('ip netns exec %s ifconfig %s up' %(ns_name,vmi_name),shell = True)
subprocess.call('ip link set %s up' %(peth), shell = True)    


subprocess.call('ovs-vsctl add-port ovs-br %s' %peth,shell = True )
