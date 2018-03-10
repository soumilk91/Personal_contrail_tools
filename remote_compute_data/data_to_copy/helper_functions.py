import sys
import json
import os
import subprocess
import paramiko
import time

if (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
    print '''
        THE CORRECT FORMAT OF USING THIS SCRIPT IS:
                python inp_to_yaml.py <input_json_file> <path to the testbed.py file>  <function_to_perform>
        EXAMPLE :
                python inp_to_yaml.py input.json /opt/contrail/utils/fabfile/testbeds/testbed.py create_network_yaml > network.yaml
        '''
    sys.exit()

# Method for checking the status of stacks during their creation phase
def get_stack_status():
    stack_name = sys.argv[1]
    a = subprocess.Popen(
        'heat stack-list | grep %s' %
        stack_name,
        shell=True,
        stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp = str(a_tmp)
    if "CREATE_FAILED" in a_tmp:
        print "failed"
    elif "CREATE_COMPLETE" in a_tmp:
        print "success"
    elif "CREATE_IN_PROGRESS" in a_tmp:
        print "inprogress"

def get_fixed_network_name():
    project_uuid = sys.argv[1]
    a = subprocess.Popen(
        'neutron net-list -f json',
        shell=True,
        stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp = str(a_tmp)
    a_tmp_list_of_dicts = json.loads(a_tmp)
    for i in a_tmp_list_of_dicts:
	if project_uuid in a_tmp_list_of_dicts[i]['name']:
	    if '10.0.' in a_tmp_list_of_dicts[i]['subnets']:
	        print a_tmp_list_of_dicts[i]['name']
 
def get_ubuntu_14_04_image_for_vms():
    a = subprocess.Popen("openstack image list -f json",shell=True,stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp_dict = eval(a_tmp)
    a_tmp = ""
    for i in a_tmp_dict:
        if i["Name"] == "ubuntu-14-04":
            a_tmp = "ubuntu-14-04"
    if len(a_tmp) == 0:
	print "Ubuntu-14-04  Image is not present in the cluster, Downloading it ----->>\n"
	a = subprocess.Popen("wget http://10.84.5.120/cs-shared/soumilk/remote_compute/Remote_compute_Automation/new_topology-try-2017-12-11/New_working_VMX/ubuntu-14-04.qcow2", shell=True, stdout=subprocess.PIPE)
	a_tmp = a.stdout.read()
	a_tmp = str(a_tmp)
	print a_tmp
    	print "Adding the Downloaded Ubuntu image to the contrail cluster"
    	a = subprocess.Popen("openstack image create --disk-format qcow2 --container-format bare --public --file ubuntu-14-04.qcow2 ubuntu-14-04", shell=True, stdout=subprocess.PIPE)
    	a_tmp = a.stdout.read()
    	print a_tmp
    	time.sleep(5)
    	a = subprocess.Popen("openstack image list | grep ubuntu-14-04", shell=True, stdout=subprocess.PIPE)
    	a_tmp = a.stdout.read()
    	print a_tmp  
    else:
	print "Ubuntu-14-04 image is already present in the cluster\n"	
 	a = subprocess.Popen("openstack image list | grep ubuntu-14-04", shell=True, stdout=subprocess.PIPE)
	a_tmp = a.stdout.read()
	print a_tmp

def get_fpc_image_for_vmx():
    a = subprocess.Popen("openstack image list -f json",shell=True,stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp_dict = eval(a_tmp)
    a_tmp = ""
    for i in a_tmp_dict:
        if i["Name"] == "fpc_181":
            a_tmp = "fpc_181"
    if len(a_tmp) == 0:
        print "FPC Image of the VMX is not present in the cluster, Downloading it ----->>\n"
        #a = subprocess.Popen('sshpass -p "c0ntrail123" scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@10.84.24.64:/cs-shared/soumilk/remote_compute/Remote_compute_Automation/new_topology-try-2017-12-11/New_working_VMX/vmx_fpc_image .', shell=True, stdout=subprocess.PIPE)
        a = subprocess.Popen("wget http://10.84.5.120/cs-shared/soumilk/remote_compute/Remote_compute_Automation/new_topology-try-2017-12-11/New_working_VMX/vmx_fpc_image", shell=True, stdout=subprocess.PIPE)
	a_tmp = a.stdout.read()
        a_tmp = str(a_tmp)
        print a_tmp
        print "Adding the Downloaded FPC image to the contrail cluster\n"
        a = subprocess.Popen("openstack image create --container-format bare --disk-format vmdk --private --property hw_cdrom_bus='ide' --property hw_disk_bus='ide' --property hw_vif_model='virtio' --file vmx_fpc_image fpc_181", shell=True, stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        print a_tmp
        time.sleep(5)
        a = subprocess.Popen("openstack image list | grep fpc_181", shell=True, stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        print a_tmp
    else:
        print "FPC image is already present in the cluster\n"
        a = subprocess.Popen("openstack image list | grep fpc_181", shell=True, stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        print a_tmp

def get_re_image_for_vmx():
    a = subprocess.Popen("openstack image list -f json",shell=True,stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp_dict = eval(a_tmp)
    a_tmp = ""
    for i in a_tmp_dict:
        if i["Name"] == "re_181":
            a_tmp = "re_181"
    if len(a_tmp) == 0:
        print "RE Image of the VMX is not present in the cluster, Downloading it ----->>\n"
        a = subprocess.Popen("wget http://10.84.5.120/cs-shared/soumilk/remote_compute/Remote_compute_Automation/new_topology-try-2017-12-11/New_working_VMX/vmx_re_image", shell=True, stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        a_tmp = str(a_tmp)
        print a_tmp
        print "Adding the Downloaded RE image to the contrail cluster\n"
        a = subprocess.Popen("openstack image create --container-format bare --disk-format qcow2 --private --property hw_cdrom_bus='ide' --property hw_disk_bus='ide' --property hw_vif_model='virtio' --file vmx_re_image re_181", shell=True, stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        print a_tmp
        time.sleep(5)
        a = subprocess.Popen("openstack image list | grep re_181", shell=True, stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        print a_tmp
    else:
        print "RE image is already present in the cluster\n"
        a = subprocess.Popen("openstack image list | grep re_181", shell=True, stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        print a_tmp

def check_required_flavors():
    print "Checking if the flavor required for Virtual Machines is present in the cluster\n"
    chk_flavor = subprocess.Popen("openstack flavor list  | grep m1.xxlarge",shell=True, stdout=subprocess.PIPE)
    chk_flavor_tmp = chk_flavor.stdout.read()
    if len(chk_flavor_tmp) == 0:
        print "The Recommended Flavor for Virtual Machines is not present on the base cluster, Adding it :-\n"
        add_flavor = subprocess.Popen("openstack flavor create m1.xxlarge --id 100 --ram 32768 --disk 300 --vcpus 10 --public",shell=True, stdout=subprocess.PIPE)
	add_flavor_tmp = add_flavor.stdout.read()
	print add_flavor_tmp
	print "Checking if the added Flavor Present on the base cluster:-\n"
	chk_flavor = subprocess.Popen("openstack flavor list | grep m1.xxlarge", shell=True, stdout=subprocess.PIPE)
	chk_flavor_tmp = chk_flavor.stdout.read()
	print chk_flavor_tmp
    else:
	print "The Recommended Flavor for the Virtual Machine is Present in the Base Cluster\n"
    print "Checking if the fpc flavor required for the VMX is present in on the base cluster \n"
    chk_flavor = subprocess.Popen("openstack flavor list  | grep pfe-more-ram",shell=True, stdout=subprocess.PIPE)
    chk_flavor_tmp = chk_flavor.stdout.read()
    if len(chk_flavor_tmp) == 0:
	print "The Recommended FPC Flavor for VMX is not present on the base cluster, Adding it :-\n"
	add_flavor = subprocess.Popen("openstack flavor create pfe-more-ram --id 1001 --ram 20480 --disk 40 --vcpus 7 --public",shell=True, stdout=subprocess.PIPE)	
	add_flavor_tmp = add_flavor.stdout.read()
	print add_flavor_tmp
	print "Checking if the added Flavor Present on the base cluster:-\n"
	chk_flavor = subprocess.Popen("openstack flavor list | grep pfe-more-ram", shell=True, stdout=subprocess.PIPE)
	chk_flavor_tmp = chk_flavor.stdout.read()
	print chk_flavor_tmp
    else:
	print "The Recommended FPC Flavor for the VMX is Present in the Base Cluster\n"
    print "Checking if the re flavor required for the VMX is present in on the base cluster \n"
    chk_flavor = subprocess.Popen("openstack flavor list  | grep re-flv",shell=True, stdout=subprocess.PIPE)
    chk_flavor_tmp = chk_flavor.stdout.read()
    if len(chk_flavor_tmp) == 0:
	print "The Recommended RE Flavor for VMX is not present on the base cluster, Adding it :-\n"
	add_flavor = subprocess.Popen("nova flavor-create --is-public true re-flv auto 4096 40 1; nova flavor-key  re-flv set  aggregate_instance_extra_specs:global-grouppinned=true ; nova flavor-key  re-flv set hw:cpu_policy=dedicated",shell=True, stdout=subprocess.PIPE)
	add_flavor_tmp = add_flavor.stdout.read()
	print add_flavor_tmp
	print "Checking if the added Flavor Present on the base cluster:-\n"
	chk_flavor = subprocess.Popen("openstack flavor list | grep re-flv", shell=True, stdout=subprocess.PIPE)
	chk_flavor_tmp = chk_flavor.stdout.read()
	print chk_flavor_tmp
    else:
	print "The Recommended RE Flavor for the VMX is Present in the Base Cluster\n"

if __name__ == '__main__':
    if len(sys.argv) == 3:
        globals()[sys.argv[2]]()
    else:
        print "Wrong Number of arguments given"
