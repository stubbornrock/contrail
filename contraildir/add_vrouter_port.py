from vnc_api import vnc_api
import subprocess

api_server = '172.16.119.143'
api_port = 8082

project = 'default-domain:default-project'
ipam_network = 'default-network-ipam'
net_name = 'demo'
subnet_name = '192.168.2.0/24'
vm_name = 'test3'
vmi_name = 'veth0'

#project name
proj_fq_name = project.split(':')

# get vnc client
vnc = vnc_api.VncApi(api_server_host=api_server,api_server_port=api_port)

#find or create vm instance
print "=========>>> CREATE VM INSTANCE ... ..."
vm_fq_name=[ vm_name ]
try:
    vm_instance = vnc.virtual_machine_read(fq_name = vm_fq_name)
    print "[SUCCESS] VM: %s Has Exsited!" %vm_name
except vnc_api.NoIdError:
    print "[WARN] VM: %s Does't Exsit! Creating ... " %vm_name
    vm_instance = vnc_api.VirtualMachine(vm_name, fq_name=vm_fq_name)
    vnc.virtual_machine_create(vm_instance)
finally:
    vm_instance = vnc.virtual_machine_read(fq_name = vm_fq_name)
    print "[INFO] VM: %s fq_name: %s" %(vm_name, vm_instance.fq_name)

# find or create the network
print "=========>>> CREATE NETWORK ... ..."
#vnet_fq_name = [u'default-domain', u'vCenter', u'vn3'])
vnet_fq_name = proj_fq_name + [ net_name ]
try:
    vnet = vnc.virtual_network_read(fq_name = vnet_fq_name)
    print "[SUCCESS] VNET: %s Has Exsited!" %net_name
except vnc_api.NoIdError:
    print "[WARN] VNET: %s Doesn't Exist! Creating ..." %net_name
    vnet = vnc_api.irtualNetwork(net_name, parent_type = 'project', fq_name = vnet_fq_name)
    # add a subnet
    subnet_fq_name = proj_fq_name + [ ipam_network ]
    ipam = vnc.network_ipam_read(subnet_fq_name)

    (prefix, plen) = subnet_name.split('/')
    subnet = vnc_api.IpamSubnetType(
                    subnet = vnc_api.SubnetType(prefix, int(plen)))
    vnet.add_network_ipam(ipam, vnc_api.VnSubnetsType([subnet]))
    vnc.virtual_network_create(vnet)
finally:
    vnet = vnc.virtual_network_read(fq_name = vnet_fq_name)
    print "[INFO] VNET: %s fq_name: %s" %(net_name,vnet.fq_name)

# find or create the vminterface
print "=========>>> CREATE VM INTERFACE ... ..."
vmi_created = False
vmi_fq_name = vm_instance.fq_name + [ vmi_name ]
try:
    vm_interface = vnc.virtual_machine_interface_read(fq_name = vmi_fq_name)
    print "[SUCCESS] VM_Interface: %s Has Exsited!" %vmi_name
except vnc_api.NoIdError:
    print "[WARN] VM_Interface: %s Doesn't Exsit! Creating ... " %vmi_name
    vm_interface = vnc_api.VirtualMachineInterface(name = vmi_name, parent_type = 'virtual-machine', fq_name = vmi_fq_name)
    vmi_created = True
finally:
    vm_interface.set_virtual_network(vnet)
    if vmi_created:
        vnc.virtual_machine_interface_create(vm_interface)
    else:
        vnc.virtual_machine_interface_update(vm_interface)
    # re-read the vmi to get its mac addresses
    vm_interface = vnc.virtual_machine_interface_read(fq_name = vmi_fq_name)
    print "[INFO] VM_Ineterface: %s fq_name: %s" %(vmi_name,vm_interface.fq_name)

# create an IP for the VMI if it doesn't already have one
print "=========>>> CONFIGURE VM INTERFACE IP INFO ... ..."
ips = vm_interface.get_instance_ip_back_refs()
print "[INFO] VM_Interface: %s 's ips:%s" %(vmi_name,ips)
if not ips:
    print "[WARN] ips is [], Creating ..."
    ip = vnc_api.InstanceIp(vm_instance.name + '.'+vmi_name)
    ip.set_virtual_machine_interface(vm_interface)
    ip.set_virtual_network(vnet)
    ip_created = vnc.instance_ip_create(ip)

# get the ip, mac, and gateway from the vmi
ip_uuid = vm_interface.get_instance_ip_back_refs()[0]['uuid']
ip = vnc.instance_ip_read(id=ip_uuid).instance_ip_address
mac = vm_interface.virtual_machine_interface_mac_addresses.mac_address[0]
subnet = vnet.network_ipam_refs[0]['attr'].ipam_subnets[0]
ipaddr = "%s/%s" %(ip,subnet.subnet.ip_prefix_len)
gw = subnet.default_gateway
dns = gw
print "[INFO] VM_INTERFACE IPINFO:\n [ip_uuid:%s,ip:%s,mac:%s,subnet:%s,gw:%s,dns:%s]" %(ip_uuid,ip,mac,ipaddr,gw,dns)

#set up the veth pair with one part for vrouter and one for the netns
print "=========>>> ADD VM NETWORK NAMESPACE ... ..."
ns_name = vm_name + 'ns'
peth = vm_name + '-peth'
print 'Execute>> ip netns delete %s' %(ns_name)
subprocess.call('ip netns delete %s' %(ns_name), shell = True)
print 'Execute>> ip netns add %s' %(ns_name)
subprocess.call('ip netns add %s' %(ns_name), shell = True)
print 'Execute>> ip netns list'
subprocess.call('ip netns list', shell = True)
print 'Execute>> ip link add %s type veth peer name %s' %(vmi_name,peth)
subprocess.call('ip link add %s type veth peer name %s' %(vmi_name,peth), shell = True)
print 'Execute>> ip link set %s netns %s' %(vmi_name,ns_name)
subprocess.call('ip link set %s netns %s' %(vmi_name,ns_name) , shell = True)
print 'Execute>> ip netns exec %s ip link set dev %s address %s' %(ns_name,vmi_name,mac)
subprocess.call('ip netns exec %s ip link set dev %s address %s' %(ns_name,vmi_name,mac), shell = True)
print 'Execute>> ip netns exec %s ip addr add %s dev %s' %(ns_name,ipaddr,vmi_name)
subprocess.call('ip netns exec %s ip addr add %s dev %s' %(ns_name,ipaddr,vmi_name), shell = True)
print 'Execute>> ip netns exec %s ifconfig %s up' %(ns_name,vmi_name)
subprocess.call('ip netns exec %s ifconfig %s up' %(ns_name,vmi_name),shell = True)
print 'Execute>> ip link set %s up' %(peth)
subprocess.call('ip link set %s up' %(peth), shell = True)    

# finally, create the Contrail port
print "=========>>> CREATE & ADD THE CONTRAIL PORT ... ..."
from contrail_vrouter_api.gen_py.instance_service import ttypes
from contrail_utils import vrouter_rpc, uuid_from_string, uuid_array_to_str


print 'Execute>> Delete port %s' %vm_interface.uuid
rpc = vrouter_rpc()
rpc.DeletePort(uuid_from_string(vm_interface.uuid))

print 'Execute>> Add port %s' %vm_interface.uuid
port = ttypes.Port(
    uuid_from_string(vm_interface.uuid),
    uuid_from_string(vm_instance.uuid),
    peth,
    ip,
    uuid_from_string(vnet.uuid),
    mac,
    )
rpc.AddPort([port])

print (dict(port_id = uuid_array_to_str(port.port_id),
            vm_id = vm_instance.uuid,
            net_id = vnet.uuid,
            vmi_id = vm_interface.uuid,
            veth = peth,
            netns = ns_name,
            ip = ip,
            mac = mac,
            gw = gw,
            dns = dns,
            netmask = subnet.subnet.ip_prefix_len,
            broadcast = subnet.subnet.ip_prefix,
            ))
