"""
Author: Soumil Kulkarni
File Name: inp_to_yaml.py
Summary: Script to create a virtualized infrastructure for running daily sanity or recreating any bugs for testing purpose. (Contrail on Contrail)
"""
import sys
import json
from fabric.api import *
import paramiko
import os
import subprocess
import ast
import uuid
import random
import string
import time

# with open("floating_ip_test_multiple.json") as json_data:
if (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
    print '''
	THE CORRECT FORMAT OF USING THIS SCRIPT IS:
		python inp_to_yaml.py <input_json_file> <function_to_perform>
	EXAMPLE :
		python inp_to_yaml.py input.json create_network_yaml > network.yaml
	'''
    sys.exit()

inp_file = sys.argv[1]
with open(inp_file) as json_data:
    parsed_json = json.load(json_data)


description = parsed_json["inp_params"]["description"]["msg"]
total_servers = parsed_json["inp_params"]["params"]["no_of_servers"]
total_networks = parsed_json["inp_params"]["params"]["no_of_networks"]

network_name_list = []
# parse all the data from the json file into a dict so that it an be used
# in the script

# Creating all The Dictionaries from the input json file that are required
# for all the functions to work properly in a scalable manner

#server_dict = parsed_json["inp_params"]["servers"]
server_dict = {}
network_dict = parsed_json["inp_params"]["networks"]
#cluster_dict = parsed_json["inp_params"]["cluster_json_params"]
cluster_dict = {}
floating_ip_network_dict = parsed_json["inp_params"]["floating_ip_network"]
general_params_dict = parsed_json["inp_params"]["params"]
#testbed_py_dict = parsed_json["inp_params"]["testbed_py_params"]
testbed_py_dict = {}
all_cluster_dict = parsed_json["inp_params"]["cluster"]

for clus in all_cluster_dict:
    server_dict[clus] = all_cluster_dict[clus]["servers"]
    cluster_dict[clus] = all_cluster_dict[clus]["cluster_json_params"]
    testbed_py_dict[clus] = all_cluster_dict[clus]["testbed_py_params"]

for i in network_dict:
    network_name_list.append(network_dict[i]["name"])
    # A list to maintain all the network names


def add_sm_os_to_openstack():
    a = subprocess.Popen(
        "openstack image list -f json",
        shell=True,
        stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp_dict = eval(a_tmp)
    a_tmp = ""
    for i in a_tmp_dict:
        if i["Name"] == "ubuntu-14-04":
            a_tmp = "ubuntu-14-04"
    if len(a_tmp) == 0:
        print "The Requested Image is not present in the cluster, Downloading it ----->>\n"
        ab = subprocess.Popen(
            "wget http://10.84.5.120/images/soumilk/vm_images/ubuntu14-04-5.qcow2",
            shell=True,
            stdout=subprocess.PIPE)
        ab_tmp = a.stdout.read()
        print a_tmp
        time.sleep(10)
        a = subprocess.Popen(
            "openstack image create --disk-format qcow2 --container-format bare --public --file ubuntu14-04-5.qcow2 ubuntu-14-04",
            shell=True,
            stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        print a_tmp
        time.sleep(5)
        a = subprocess.Popen(
            "openstack image list | grep ubuntu-14-04",
            shell=True,
            stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        print a_tmp
    else:
        print "Requested Image already exists in the cluster "


def check_if_sm_has_correct_image():
    for clus in server_dict:
        for server in server_dict[clus]:
            if server_dict[clus][server]["server_manager"] == "true":
                # First change the image_val in input.json
                server_dict[clus][server]["image"] = "ubuntu-14-04"
                print server_dict[clus][server]
                a = subprocess.Popen(
                    "openstack image list -f json",
                    shell=True,
                    stdout=subprocess.PIPE)
                a_tmp = a.stdout.read()
                a_tmp_dict = eval(a_tmp)
                a_tmp = ""
                for i in a_tmp_dict:
                    if i["Name"] == "ubuntu-14-04":
                        a_tmp = "ubuntu-14-04"
                if len(a_tmp) == 0:
                    b = subprocess.Popen(
                        "wget http://10.84.5.120/images/soumilk/vm_images/ubuntu14-04-5.qcow2",
                        shell=True,
                        stdout=subprocess.PIPE)
                    b_tmp = b.stdout.read()
                    print b_tmp
                    print "Image for server manager downloaded"
                    a = subprocess.Popen(
                        "openstack image create --disk-format qcow2 --container-format bare --public --file ubuntu14-04-5.qcow2 ubuntu-14-04",
                        shell=True,
                        stdout=subprocess.PIPE)
                    a_tmp = a.stdout.read()
                    print a_tmp

                else:
                    print "Server Image already exists in the cluster"

# A method for checking if the required falvor exists in the openstack, if
# not creating it.


def check_and_create_required_flavor():
    print "Checking Flavor for servers"
    chk_flavor = subprocess.Popen(
        "openstack flavor list  | grep m1.xxlarge",
        shell=True,
        stdout=subprocess.PIPE)
    chk_flavor_tmp = chk_flavor.stdout.read()
    if len(chk_flavor_tmp) == 0:
        print "The Recommended Flavor is not present on the base cluster, Adding it :-\n"
        add_flavor = subprocess.Popen(
            "openstack flavor create m1.xxlarge --id 100 --ram 32768 --disk 300 --vcpus 10 --public",
            shell=True,
            stdout=subprocess.PIPE)
        add_flavor_tmp = add_flavor.stdout.read()
        print add_flavor_tmp
        print "Printing all the Flavors Present on the base cluster:-"
        chk_flavor = subprocess.Popen(
            "openstack flavor list | grep m1.xxlarge",
            shell=True,
            stdout=subprocess.PIPE)
        chk_flavor_tmp = chk_flavor.stdout.read()
        print chk_flavor_tmp
    else:
        print "The Recommended Flavor is Present in the Base Cluster"
        chk_flavor = subprocess.Popen(
            "openstack flavor list | grep m1.xxlarge",
            shell=True,
            stdout=subprocess.PIPE)
        chk_flavor_tmp = chk_flavor.stdout.read()
        print chk_flavor_tmp

    print "Checking Flavor re-flv for vMX to work"
    chk_flavor = subprocess.Popen(
        "openstack flavor list  | grep re-flv",
        shell=True,
        stdout=subprocess.PIPE)
    chk_flavor_tmp = chk_flavor.stdout.read()
    if len(chk_flavor_tmp) == 0:
        print "The Recommended Flavor is not present on the base cluster, Adding it :-\n"
        add_flavor = subprocess.Popen(
            "nova flavor-create --is-public true re-flv auto 4096 40 1; nova flavor-key  re-flv set  aggregate_instance_extra_specs:global-grouppinned=true ; nova flavor-key  re-flv set hw:cpu_policy=dedicated",
            shell=True,
            stdout=subprocess.PIPE)
        add_flavor_tmp = add_flavor.stdout.read()
        print add_flavor_tmp
        chk_flavor = subprocess.Popen(
            "openstack flavor list | grep re-flv",
            shell=True,
            stdout=subprocess.PIPE)
        chk_flavor_tmp = chk_flavor.stdout.read()
        print chk_flavor_tmp
    else:
        print "The Recommended re-flv  Flavor is Present in the Base Cluster"
        chk_flavor = subprocess.Popen(
            "openstack flavor list | grep re-flv",
            shell=True,
            stdout=subprocess.PIPE)
        chk_flavor_tmp = chk_flavor.stdout.read()
        print chk_flavor_tmp

    print "Checking Flavor pfe-flv for vMX to work"
    chk_flavor = subprocess.Popen(
        "openstack flavor list  | grep pfe-flv",
        shell=True,
        stdout=subprocess.PIPE)
    chk_flavor_tmp = chk_flavor.stdout.read()
    if len(chk_flavor_tmp) == 0:
        print "The Recommended Flavor is not present on the base cluster, Adding it :-\n"
        add_flavor = subprocess.Popen(
            "nova flavor-create --is-public true pfe-flv auto 16384 40 7 ; nova flavor-key  pfe-flv set  aggregate_instance_extra_specs:global-grouppinned=true ; nova flavor-key  pfe-flv set hw:cpu_policy=dedicated",
            shell=True,
            stdout=subprocess.PIPE)
        add_flavor_tmp = add_flavor.stdout.read()
        print add_flavor_tmp
        chk_flavor = subprocess.Popen(
            "openstack flavor list | grep pfe-flv",
            shell=True,
            stdout=subprocess.PIPE)
        chk_flavor_tmp = chk_flavor.stdout.read()
        print chk_flavor_tmp
    else:
        print "The Recommended pfe-flv  Flavor is Present in the Base Cluster"
        chk_flavor = subprocess.Popen(
            "openstack flavor list | grep pfe-flv",
            shell=True,
            stdout=subprocess.PIPE)
        chk_flavor_tmp = chk_flavor.stdout.read()
        print chk_flavor_tmp
    
    print "Checking Flavor pfe-more-ram for vMX to work"
    chk_flavor = subprocess.Popen(
        "openstack flavor list  | grep pfe-more-ram",
        shell=True,
        stdout=subprocess.PIPE)
    chk_flavor_tmp = chk_flavor.stdout.read()
    if len(chk_flavor_tmp) == 0:
        print "The Recommended Flavor is not present on the base cluster, Adding it :-\n"
        add_flavor = subprocess.Popen(
	    "openstack flavor create pfe-more-ram --id 1001 --ram 20480 --disk 40 --vcpus 7 --public",
	    shell=True,
	    stdout=subprocess.PIPE)
	add_flavor_tmp = add_flavor.stdout.read()
	print add_flavor_tmp
	chk_flavor = subprocess.Popen(
	    "openstack flavor list | grep pfe-more-ram",
	    shell=True,
	    stdout=subprocess.PIPE)
	chk_flavor_tmp = chk_flavor.stdout.read()
	print chk_flavor_tmp
    else:
	print "The Recommended pfe-more-ram Flavor is Present in the Base Cluster"
	chk_flavor = subprocess.Popen(
	    "openstack flavor list | grep pfe-more-ram",
	    shell=True,
	    stdout=subprocess.PIPE)
	chk_flavor_tmp = chk_flavor.stdout.read()
	print chk_flavor_tmp


# A method for adding the project UUID in the names of the of all the
# networks so that they won't create duplicates


def change_network_dict():
    project_uuid = general_params_dict["project_uuid"]
    # print project_uuid
    for k in network_dict:
        if project_uuid not in k:
            new_key = k + "_" + project_uuid
            network_dict[new_key] = network_dict.pop(k)
    # print network_dict
    for i in network_dict:
        name = network_dict[i]["name"]
        if project_uuid not in name:
            new_name = name + "_" + project_uuid
            network_dict[i]["name"] = new_name
    # print network_dict

# A Method for chnaginf the network and the server stack names


def change_stack_names():
    project_uuid = general_params_dict["project_uuid"]
    general_params_dict["network_stack_name"] = general_params_dict["network_stack_name"] + project_uuid
    general_params_dict["server_stack_name"] = general_params_dict["server_stack_name"] + project_uuid

# A method to create a yaml file to create networks using the heat
# component of the openstack


def create_network_yaml():
    change_network_dict()
    project_uuid = general_params_dict["project_uuid"]
    network_string = ""
    network_string = network_string + "heat_template_version: 2015-04-30\n\ndescription: " + \
        description + "\n\n" + "resources:\n"
    for i in network_dict:
        num = 1
        if "name" in network_dict[i]:
            name = network_dict[i]["name"]
        else:
            name = i
        network_name_list.append(name)
        network_string = network_string + "  " + name + ":\n"
        network_string = network_string + "    type: OS::Neutron::Net\n"
        network_string = network_string + "    properties:\n      name: " + name + "\n"
        network_string = network_string + "      tenant_id: %s\n\n" % project_uuid
        subnet_name = name + "_subnet_" + str(num)
        network_string = network_string + "  " + subnet_name + ":\n"
        network_string = network_string + "    type: OS::Neutron::Subnet\n"
        network_string = network_string + "    properties:\n"
        network_string = network_string + "      tenant_id: %s\n" % project_uuid
        network_string = network_string + \
            "      network_id: { get_resource: %s }\n" % name
        ip_block_with_mask = network_dict[i]["ip_block_with_mask"]
        network_string = network_string + "      cidr: %s\n" % ip_block_with_mask
        network_string = network_string + "      ip_version: 4\n"
        network_string = network_string + "      name: %s\n\n" % subnet_name
        num = num + 1
    print network_string


# A Method for changing the server_dict according to the given
# 'project_uuid' given in the 'input.json' file so that naming
# complications can be avoided.
def change_server_dict():
    for clus in all_cluster_dict:
        server_dict = parsed_json["inp_params"]["cluster"][clus]["servers"]
        project_uuid = general_params_dict["project_uuid"]
        # print server_dict
        for i in server_dict:
            if project_uuid not in i:
                new_key = i + "_" + project_uuid
                server_dict[new_key] = server_dict.pop(i)

        # print server_dict
        for i in server_dict:
            a = server_dict[i]['ip_address']
            for j in a:
                if project_uuid not in j:
                    new_key = j + "_" + project_uuid
                    a[new_key] = a.pop(j)
    # print server_dict

# A Method for changing the floatingIP pool parameters from the input.json


def change_floatingip_pool_params():
    project_uuid = general_params_dict["project_uuid"]
    name = floating_ip_network_dict["param"]["name"]
    if project_uuid not in name:
        new_name = name + "_" + project_uuid
        floating_ip_network_dict["param"]["name"] = new_name
    return floating_ip_network_dict


# A Method to create a yaml file to create servers using the heat
# component of the openstack
def create_server_yaml():
    final_server_yaml_string = ""
    final_server_yaml_string = final_server_yaml_string + "heat_template_version: 2015-04-30 \n"
    final_server_yaml_string = final_server_yaml_string + "description: " + description + "\n\n"
    final_server_yaml_string = final_server_yaml_string + "resources:\n"
    change_server_dict()
    #print server_dict
    change_network_dict()
    change_stack_names()
    floating_ip_network_dict = change_floatingip_pool_params()
    #print floating_ip_network_dict
    if "floating_ip_network" in parsed_json["inp_params"]:
        name = floating_ip_network_dict["param"]["name"]
        fip_uuid = floating_ip_network_dict["param"]["floating_ip_network_uuid"]
        final_server_yaml_string = final_server_yaml_string + "  %s:\n" %name
        final_server_yaml_string = final_server_yaml_string + "    type: OS::ContrailV2::FloatingIpPool\n"
        final_server_yaml_string = final_server_yaml_string + "    properties:\n"
        final_server_yaml_string = final_server_yaml_string + "      name: %s\n" % name
        final_server_yaml_string = final_server_yaml_string + "      virtual_network: %s\n" %fip_uuid
    ip_port_dict = {}
    for clus in server_dict:
        server_string = ""
        for i in server_dict[clus]:
            #lets create ports for the server according to the template given
            indi_server_string = ""
            name = server_dict[clus][i]["name"]
            individual_ip_address_dict = server_dict[clus][i]["ip_address"]
            project_uuid = general_params_dict["project_uuid"]
            #print individual_ip_address_dict
            networks_connected_server = individual_ip_address_dict.keys()
            for net in networks_connected_server:
                if network_dict[net]["role"] == "management":
                    ip_num = 0
                elif network_dict[net]["role"] == "control-data":
                    ip_num = 1
                else:
                    ip_num = 2
                net_name = net
                port_name = name + "_port_" + str(ip_num)
                final_server_yaml_string = final_server_yaml_string + "  %s:\n" % port_name
                final_server_yaml_string = final_server_yaml_string + "    type: OS::Neutron::Port\n"
                final_server_yaml_string = final_server_yaml_string + "    properties:\n"
                final_server_yaml_string = final_server_yaml_string + "      network: %s\n" % net_name
                final_server_yaml_string = final_server_yaml_string + "      name: %s\n" %port_name
                if "mac_address" in server_dict[clus][i]:
                    final_server_yaml_string = final_server_yaml_string + "      mac_address: %s\n" %server_dict[clus][i]["mac_address"][net_name]
                final_server_yaml_string = final_server_yaml_string + "      fixed_ips:\n"
                final_server_yaml_string = final_server_yaml_string + "      - ip_address: %s\n" %individual_ip_address_dict[net_name]
                if network_dict[net]["role"] == "management":
                    final_server_yaml_string = final_server_yaml_string + "      allowed_address_pairs:\n"
                    if (("external_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) or ("contrail_external_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
                        if (("external_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and ("contrail_external_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
                            final_server_yaml_string = final_server_yaml_string + "        - ip_address: %s\n" %cluster_dict[clus]["parameters"]["provision"]["openstack"]["external_vip"]
                            final_server_yaml_string = final_server_yaml_string + "        - ip_address: %s\n" %cluster_dict[clus]["parameters"]["provision"]["contrail"]["contrail_external_vip"]
                        elif (("external_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and ("contrail_external_vip" not in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
                            final_server_yaml_string = final_server_yaml_string + "        - ip_address: %s\n" %cluster_dict[clus]["parameters"]["provision"]["openstack"]["external_vip"]
                        elif (("external_vip" not in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and ("contrail_external_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
                            final_server_yaml_string = final_server_yaml_string + "        - ip_address: %s\n" %cluster_dict[clus]["parameters"]["provision"]["contrail"]["contrail_external_vip"]

                if network_dict[net]["role"] == "control-data":
                    final_server_yaml_string = final_server_yaml_string + "      allowed_address_pairs:\n"
                    if (("internal_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) or ("contrail_internal_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
                        if (("internal_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and ("contrail_internal_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
                            final_server_yaml_string = final_server_yaml_string + "        - ip_address: %s\n" %cluster_dict[clus]["parameters"]["provision"]["openstack"]["internal_vip"]
                            final_server_yaml_string = final_server_yaml_string + "        - ip_address: %s\n" %cluster_dict[clus]["parameters"]["provision"]["contrail"]["contrail_internal_vip"]
                        elif (("internal_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and ("contrail_internal_vip" not in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
                            final_server_yaml_string = final_server_yaml_string + "        - ip_address: %s\n" %cluster_dict[clus]["parameters"]["provision"]["openstack"]["internal_vip"]
                        elif (("internal_vip" not in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and ("contrail_internal_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
                            final_server_yaml_string = final_server_yaml_string + "        - ip_address: %s\n" %cluster_dict[clus]["parameters"]["provision"]["contrail"]["contrail_internal_vip"]
                ip_port_dict[individual_ip_address_dict[net_name]] = port_name
            # lets create the servers according to the teplate given
            final_server_yaml_string = final_server_yaml_string + "  " + name + ":\n"
            final_server_yaml_string = final_server_yaml_string + "    type: OS::Nova::Server\n"
            final_server_yaml_string = final_server_yaml_string + "    properties:\n"
            final_server_yaml_string = final_server_yaml_string + "      name: %s\n" %name
            final_server_yaml_string = final_server_yaml_string + "      flavor: %s\n" %server_dict[clus][i]["flavor"]
            final_server_yaml_string = final_server_yaml_string + "      image: %s\n" %server_dict[clus][i]["image"]
            if "user_data_file_name" in server_dict[clus][i]:
                final_server_yaml_string = final_server_yaml_string + "      user_data:\n"
                final_server_yaml_string = final_server_yaml_string + "        get_file: %s\n" %server_dict[clus][i]["user_data_file_name"]
            final_server_yaml_string = final_server_yaml_string + "      networks:\n"
            ip_list = individual_ip_address_dict.values()
            ip_for_floating_ip_association = []
            ip_list.sort()
            #print ip_port_dict
            for key, value in individual_ip_address_dict.items():
                if value in ip_list:
                    if network_dict[key]["role"] == "management":
                        ip_for_floating_ip_association.append(value)
                        final_server_yaml_string = final_server_yaml_string + "        - port: { get_resource:  %s}\n" %ip_port_dict[value]
                        ip_list.remove(value)
                        #print ip_list
            if len(ip_list) > 0: 
                for j in ip_list:
                    final_server_yaml_string = final_server_yaml_string + "        - port: { get_resource:  %s}\n" %ip_port_dict[j]

            # lets create attach fip to the portif configured in the template
            if server_dict[clus][i]["floating_ip"] == "true":
                name = name + "_floating_ip"
                final_server_yaml_string = final_server_yaml_string + "  %s:\n" %name
                final_server_yaml_string = final_server_yaml_string + "    type: OS::ContrailV2::FloatingIp\n"
                final_server_yaml_string = final_server_yaml_string + "    properties:\n"
                port_for_association = ip_port_dict[ip_for_floating_ip_association[0]]
                #print port_for_association
                final_server_yaml_string = final_server_yaml_string + "      virtual_machine_interface_refs: [{ get_resource : %s}]\n" % port_for_association
                final_server_yaml_string = final_server_yaml_string + "      floating_ip_pool: { get_resource: %s }\n" %floating_ip_network_dict["param"]["name"]
                final_server_yaml_string = final_server_yaml_string + "      floating_ip_fixed_ip_address: %s\n" % ip_for_floating_ip_association[0]
                final_server_yaml_string = final_server_yaml_string + "      project_refs: [ %s ]\n" %project_uuid
            else:
                continue

	    # Lets create and attach extra volumes to the server is configured in the template
	    if "attach_extra_volume" in server_dict[clus][i]:
		name_volume = server_dict[clus][i]["name"] + "_cinder_volume"
		final_server_yaml_string = final_server_yaml_string + "  %s:\n" %name_volume
		final_server_yaml_string = final_server_yaml_string + "    type: OS::Cinder::Volume\n"
		final_server_yaml_string = final_server_yaml_string + "    properties:\n"
		final_server_yaml_string = final_server_yaml_string + "      size: %d\n" %server_dict[clus][i]["attach_extra_volume"]
		final_server_yaml_string = final_server_yaml_string + "      name: %s\n" %name_volume
		name_attachment = server_dict[clus][i]["name"] + "_volume_attachment"
		final_server_yaml_string = final_server_yaml_string + "  %s:\n" %name_attachment
		final_server_yaml_string = final_server_yaml_string + "    type: OS::Cinder::VolumeAttachment\n"
		final_server_yaml_string = final_server_yaml_string + "    properties:\n"
		final_server_yaml_string = final_server_yaml_string + "      volume_id: { get_resource: %s }\n" %name_volume
		final_server_yaml_string = final_server_yaml_string + "      instance_uuid: { get_resource: %s }\n" %server_dict[clus][i]["name"]

    print final_server_yaml_string



# Method for Parsing Openstack Resource output
fixed_ip_mac_mapping = {}
# Dict for storing fixed IP to Mac mapping
# floating_ip_mac_mapping is for the mapping of the floating ip to the
# server manager VM so that it can be used in the provisioning of the
# server manager vm
floating_ip_mac_mapping = {}


def parse_output():
    project_uuid = general_params_dict["project_uuid"]
    # Change the contents of the Server_dict
    change_server_dict()
    # Change the contets of the Network_dict
    change_network_dict()
    # Change the contents of the floating_ip_network_dict
    floating_ip_network_dict = change_floatingip_pool_params()
    # Change both the stack names
    change_stack_names()
    network_stack_name = general_params_dict["network_stack_name"]
    server_stack_name = general_params_dict["server_stack_name"]
    # print network_stack_name
    # print server_stack_name
    all_server_names = []
    for clus in server_dict:
        for i in server_dict[clus]:
            name = server_dict[clus][i]["name"]
            all_server_names.append(name)
    # print all_server_names
    # print server_stack_name
    for i in all_server_names:
        #a = os.system("openstack stack resource show %s %s"%(server_stack_name,i))
        a = subprocess.Popen(
            "openstack stack resource show %s %s" %
            (server_stack_name, i), shell=True, stdout=subprocess.PIPE)
        a_tmp = a.stdout.read()
        a_tmp = str(a_tmp)
        # print a_tmp
        split_list_1 = a_tmp.split("attributes")
        # print split_list_1
        split_string_1 = split_list_1[1]
        # print split_string_1
        split_list_2 = split_string_1.split("creation_time")
        # print split_list_2[0]
        split_string_2 = split_list_2[0]
        split_list_3 = split_string_2.split("|")
        # print split_list_3
        final_string = split_list_3[1]
        final_string.replace(" ", "")
        # print final_string
        # Convert the above string 'final_string' into a valid dictionary
        final_resource_params_dict = eval(final_string)
        # print final_resource_params_dict["addresses"]
        for j in final_resource_params_dict["addresses"]:
            # print j
            for k in range(len(final_resource_params_dict["addresses"][j])):
                # print k
                # print final_resource_params_dict["addresses"][j]
                if final_resource_params_dict["addresses"][j][k]["OS-EXT-IPS:type"] == "fixed":
                    fixed_ip_mac_mapping[final_resource_params_dict["addresses"][j][k]["addr"]
                                         ] = final_resource_params_dict["addresses"][j][k]["OS-EXT-IPS-MAC:mac_addr"]
                    # print "Yes"
                elif final_resource_params_dict["addresses"][j][k]["OS-EXT-IPS:type"] == "floating":
                    floating_ip_mac_mapping[final_resource_params_dict["addresses"][j][k][
                        "OS-EXT-IPS-MAC:mac_addr"]] = final_resource_params_dict["addresses"][j][k]["addr"]
    # print fixed_ip_mac_mapping
    # print floating_ip_mac_mapping

# A Method for gettinf the server manager ip


def get_sm_ip():
    fixedip_to_floatingip_mapping_dict = {}
    ret_dict = {}
    project_uuid = general_params_dict["project_uuid"]
    a = subprocess.Popen('neutron floatingip-list --tenant_id %s -f json' %
                         project_uuid, shell=True, stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp = str(a_tmp)
    change_network_dict()
    fip_neutron_dict = eval(a_tmp)
    for i in range(len(fip_neutron_dict)):
        fixedip_to_floatingip_mapping_dict[fip_neutron_dict[i]
                                           ["fixed_ip_address"]] = fip_neutron_dict[i]["floating_ip_address"]
    for clus in server_dict:
        for i in server_dict[clus]:
            name = server_dict[clus][i]["name"]
            if server_dict[clus][i]["server_manager"] == "true":
                for j in server_dict[clus][i]["ip_address"]:
                    if server_dict[clus][i]["ip_address"][j] in fixedip_to_floatingip_mapping_dict:
                        ret_dict[name] = fixedip_to_floatingip_mapping_dict[server_dict[clus]
                                                                            [i]["ip_address"][j]]
                        print fixedip_to_floatingip_mapping_dict[server_dict[clus][i]["ip_address"][j]]
                        break
                break
        break

# Method for getting floating ips of all the servers so that can be used
# in the testbed.py


def get_all_fip_dict():
    fixedip_to_floatingip_mapping_dict = {}
    ret_dict = {}
    project_uuid = general_params_dict["project_uuid"]
    a = subprocess.Popen('neutron floatingip-list --tenant_id %s -f json' %
                         project_uuid, shell=True, stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp = str(a_tmp)
    fip_neutron_dict = eval(a_tmp)
    # print fip_neutron_dict
    for i in range(len(fip_neutron_dict)):
        fixedip_to_floatingip_mapping_dict[fip_neutron_dict[i]
                                           ["fixed_ip_address"]] = fip_neutron_dict[i]["floating_ip_address"]
    # print fixedip_to_floatingip_mapping_dict
    for clus in server_dict:
        for i in server_dict[clus]:
            name = server_dict[clus][i]["name"]
            for j in server_dict[clus][i]["ip_address"]:
                if server_dict[clus][i]["ip_address"][j] in fixedip_to_floatingip_mapping_dict:
                    ret_dict[name] = fixedip_to_floatingip_mapping_dict[server_dict[clus]
                                                                        [i]["ip_address"][j]]
    return ret_dict


# A Method for gettinf the config node ip
def get_config_node_ip_mainline():
    fixedip_to_floatingip_mapping_dict = {}
    ret_dict = {}
    project_uuid = general_params_dict["project_uuid"]
    a = subprocess.Popen('neutron floatingip-list --tenant_id %s -f json' %
                         project_uuid, shell=True, stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp = str(a_tmp)
    fip_neutron_dict = eval(a_tmp)
    # print fip_neutron_dict
    for i in range(len(fip_neutron_dict)):
        fixedip_to_floatingip_mapping_dict[fip_neutron_dict[i]
                                           ["fixed_ip_address"]] = fip_neutron_dict[i]["floating_ip_address"]
    for clus in server_dict:
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                if "contrail-controller" in server_dict[clus][i]["roles"]:
                    for j in server_dict[clus][i]["ip_address"]:
                        if server_dict[clus][i]["ip_address"][j] in fixedip_to_floatingip_mapping_dict:
                            ret_dict["contrail-controller"] = fixedip_to_floatingip_mapping_dict[server_dict[clus]
                                                                                                 [i]["ip_address"][j]]
    print ret_dict["contrail-controller"]


def get_config_node_ip():
    fixedip_to_floatingip_mapping_dict = {}
    ret_dict = {}
    project_uuid = general_params_dict["project_uuid"]
    a = subprocess.Popen('neutron floatingip-list --tenant_id %s -f json' %
                         project_uuid, shell=True, stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp = str(a_tmp)
    fip_neutron_dict = eval(a_tmp)
    # print fip_neutron_dict
    for i in range(len(fip_neutron_dict)):
        fixedip_to_floatingip_mapping_dict[fip_neutron_dict[i]
                                           ["fixed_ip_address"]] = fip_neutron_dict[i]["floating_ip_address"]
    for clus in server_dict:
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                if "config" in server_dict[clus][i]["roles"]:
                    for j in server_dict[clus][i]["ip_address"]:
                        if server_dict[clus][i]["ip_address"][j] in fixedip_to_floatingip_mapping_dict:
                            ret_dict["config"] = fixedip_to_floatingip_mapping_dict[server_dict[clus]
                                                                                    [i]["ip_address"][j]]
    print ret_dict["config"]

# Method for creatng server.json required for the mainline build


def create_server_json_mainline():
    parse_output()
    change_network_dict()
    floating_ip_network_dict = change_floatingip_pool_params()
    change_stack_names()
    server_json_string = '''{
        "server":[
        '''
    mac_address_list = []
    for i in fixed_ip_mac_mapping:
        mac_address_list.append(fixed_ip_mac_mapping[i])
    total_server_number = 0
    for clus in server_dict:
        total_server_number = total_server_number + len(server_dict[clus])
    total_server_number = total_server_number
    for clus in server_dict:
	for i in server_dict[clus]:
	    if server_dict[clus][i]["server_manager"] == "true":
		total_server_number = total_server_number - 1 
    all_server_fip_dict = get_all_fip_dict()
    #print total_server_number
    #sys.exit(0)
    #print all_server_fip_dict
    for clus in server_dict:
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                single_server_string = '\t{\n'
                if "cluster_id" in cluster_dict[clus]:
                    single_server_string = single_server_string + \
                        '\t\t"cluster_id": "%s",\n' % cluster_dict[clus]["cluster_id"]
                single_server_string = single_server_string + \
                    '\t\t"id": "%s",\n' % server_dict[clus][i]["name"]
                if "domain" in cluster_dict[clus]["parameters"]:
                    single_server_string = single_server_string + \
                        '\t\t"domain": "%s",\n' % cluster_dict[clus]["parameters"]["domain"]
                if "ipmi_address" in cluster_dict[clus]:
                    single_server_string = single_server_string + \
                        '\t\t"ipmi_address": "%s",\n' % cluster_dict[clus]["ipmi_address"]
                else:
                    single_server_string = single_server_string + '\t\t"ipmi_address": null,\n'
                if "ipmi_username" in cluster_dict[clus]:
                    single_server_string = single_server_string + \
                        '\t\t"ipmi_username": "%s",\n' % cluster_dict[clus]["ipmi_username"]
                else:
                    single_server_string = single_server_string + '\t\t"ipmi_username": null,\n'
                if "ipmi_password" in cluster_dict[clus]:
                    single_server_string = single_server_string + \
                        '\t\t"ipmi_password": "%s",\n' % cluster_dict[clus]["ipmi_password"]
                else:
                    single_server_string = single_server_string + '\t\t"ipmi_password": null,\n'
                if "control_data_iterface" in cluster_dict[clus]:
                    single_server_string = single_server_string + \
                        '\t\t"contrail": {\n'
                    single_server_string = single_server_string + \
                        '\t\t\t"control_data_interface": "%s"\n' % cluster_dict[
                            clus]["control_data_iterface"]
                    single_server_string = single_server_string + '\t\t},\n'
                # Now lets get all the network interface parameters and add
                # them to the server.json
                single_server_string = single_server_string + \
                    '\t\t"network": {\n'
                single_server_string = single_server_string + \
                    '\t\t\t"interfaces": [\n'
                total_server_interfaces = len(
                    server_dict[clus][i]["ip_address"])
                for j in (server_dict[clus][i]["ip_address"]):
                    current_network = j
                    gateway = network_dict[j]["default_gateway"]
                    ip_add = server_dict[clus][i]["ip_address"][j]
                    mask = network_dict[j]["ip_block_with_mask"]
                    mask_list = mask.split("/")
                    mask = mask_list[1]
                    ip_add_with_mask = ip_add + '/' + mask
                    mac_address = fixed_ip_mac_mapping[ip_add]
                    role = network_dict[j]["role"]
                    single_server_string = single_server_string + '\t\t\t\t{\n'
		    if role == "management":
                        int_name = cluster_dict[clus]["management_interface"]
			single_server_string = single_server_string + \
			    '\t\t\t\t\t"default_gateway": "%s",\n' % gateway
		    elif role == "kolla-network":
			int_name = cluster_dict[clus]["kolla_network_interface"]
                    else:
                        int_name = cluster_dict[clus]["control_data_iterface"]
                    #single_server_string = single_server_string + '\t\t\t\t{\n'
                    #single_server_string = single_server_string + \
                    #    '\t\t\t\t\t"default_gateway": "%s",\n' % gateway
                    single_server_string = single_server_string + \
                        '\t\t\t\t\t"ip_address": "%s",\n' % ip_add_with_mask
		    # If this an Ocata Job, MAC Address should be extracted in a different way.
		    
		    #if "kolla_network_interface" in cluster_dict[clus]:
		    	#temp_server_name = server_dict[clus][i]["name"] 
		        #temp_fip_server = all_server_fip_dict[temp_server_name]
		    	#client = paramiko.SSHClient()
		    	#client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		    	#client.connect(temp_fip_server, username = 'root', password = 'c0ntrail123')
		    	#stdin, stdout, stderr = client.exec_command('ifconfig -a | grep %s' % int_name)
		    	#temp_out_string = stdout.readlines()
			#print temp_out_string
			#print "____________"	
			#temp_str_split = temp_out_string[0].split("HWaddr")
			#print temp_str_split[1]
			#temp_str_1 = temp_str_split[1].replace(' ', '')
			#temp_str_2 = temp_str_1.replace('\n', '')
			#print temp_str_2
			#mac_address = temp_str_2
                    single_server_string = single_server_string + \
                        '\t\t\t\t\t"mac_address": "%s",\n' % mac_address
                    if "mtu" in cluster_dict[clus]:
			single_server_string = single_server_string + \
			    '\t\t\t\t\t"mtu": %s,\n' % cluster_dict[clus]["mtu"]
		    if "server_json_dhcp" in cluster_dict[clus]:
                        single_server_string = single_server_string + \
                            '\t\t\t\t\t"dhcp": %s,\n' % cluster_dict[clus]["server_json_dhcp"]
                    else:
                        single_server_string = single_server_string + '\t\t\t\t\t"dhcp": false,\n'
                    single_server_string = single_server_string + \
                        '\t\t\t\t\t"name": "%s"\n' % int_name
                    if total_server_interfaces > 1:
                        single_server_string = single_server_string + '\t\t\t\t},\n'
                    else:
                        single_server_string = single_server_string + '\t\t\t\t}\n'
                    total_server_interfaces = total_server_interfaces - 1
                single_server_string = single_server_string + "\t\t\t],\n"
                if "provisioning_type" in cluster_dict[clus]:
                    single_server_string = single_server_string + \
                        '\t\t\t"provisioning_type": "%s",\n' % cluster_dict[clus]["provisioning_type"]
                if "management_interface" in cluster_dict[clus]:
                    single_server_string = single_server_string + \
                        '\t\t\t"management_interface": "%s"\n' % cluster_dict[
                            clus]["management_interface"]
                single_server_string = single_server_string + '\t\t},\n'
                single_server_string = single_server_string + \
                    '\t\t"password": "%s",\n' % cluster_dict[clus]["server_password"]
                role_string = '['
                no_of_roles = len(server_dict[clus][i]["roles"])
                for r in server_dict[clus][i]["roles"]:
                    if no_of_roles == 1:
                        role_string = role_string + ' "%s"' % r
                    else:
                        role_string = role_string + ' "%s",' % r
                        no_of_roles = no_of_roles - 1
                role_string = role_string + ' ]'
                single_server_string = single_server_string + '\t\t"roles": %s,\n' % role_string
                if "partition" in server_dict[clus][i]:
                    single_server_string = single_server_string + \
                        '\t\t"parameters": {\n'
                    single_server_string = single_server_string + \
                        '\t\t\t"partition": "%s"\n' % server_dict[clus][i]["partition"]
                    single_server_string = single_server_string + '\t\t}\n'
                else:
                    single_server_string = single_server_string + \
                        '\t\t"parameters": {\n'
                    single_server_string = single_server_string + '\t\t}\n'
                if total_server_number > 1:
                    single_server_string = single_server_string + '\t\t},\n'
                    total_server_number = total_server_number - 1
                else:
                    single_server_string = single_server_string + '\t\t}\n'
		#print total_server_number
                server_json_string = server_json_string + single_server_string
    server_json_string = server_json_string + '\t]\n'
    server_json_string = server_json_string + '}\n'
    print server_json_string


# Method for creating the server json required for adding the servers to
# the server manager
def create_server_json():
    parse_output()
    # Change the contents of the Server_dict
    # change_server_dict()
    # Change the contets of the Network_dict
    change_network_dict()
    # Change the contents of the floating_ip_network_dict
    floating_ip_network_dict = change_floatingip_pool_params()
    # Change the Cluster Names
    change_stack_names()
    server_json_string = '''{
	"server":[
	'''
    # Call the parse_output function os that we can use the IP-Mac Mapping provided by the function
    # parse_output()
    mac_address_list = []
    for i in fixed_ip_mac_mapping:
        mac_address_list.append(fixed_ip_mac_mapping[i])
    # print mac_address_list
    """
	for i in mac_address_list:
		if i in floating_ip_mac_mapping:
			ipmi_ip = floating_ip_mac_mapping[i]
	"""
    #total_server_number = len(parsed_json["inp_params"]["servers"]) -1
    total_server_number = 0
    for clus in server_dict:
        total_server_number = total_server_number + len(server_dict[clus])
    total_server_number = total_server_number - 1

    for clus in server_dict:
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                single_server_string = '''
				{
				"cluster_id": "%s",
				"contrail": {
					"control_data_interface": "%s"
				},
				"host_name": "%s",
				"id": "%s",
				"domain": "%s",
				"network": {
				''' % (cluster_dict[clus]["cluster_id"], cluster_dict[clus]["control_data_iterface"], server_dict[clus][i]["name"], server_dict[clus][i]["name"], cluster_dict[clus]["parameters"]["domain"])
                single_server_string = single_server_string + \
                    '''       "interfaces": ['''
                total_server_interfaces = len(
                    server_dict[clus][i]["ip_address"])
                for j in (server_dict[clus][i]["ip_address"]):
                    current_network = j
                    gateway = network_dict[j]["default_gateway"]
                    ip_add = server_dict[clus][i]["ip_address"][j]
                    mask = network_dict[j]["ip_block_with_mask"]
                    mask_list = mask.split("/")
                    mask = mask_list[1]
                    mac_address = fixed_ip_mac_mapping[ip_add]
                    role = network_dict[j]["role"]
                    if role == "management":
                        int_name = cluster_dict[clus]["management_interface"]
                    else:
                        int_name = cluster_dict[clus]["control_data_iterface"]
                    if total_server_interfaces > 1:
			if "mtu" in cluster_dict[clus]:
                                single_server_string = single_server_string + '''
                                        {
                                                        "default_gateway": "%s",
                                                        "dhcp": false,
                                                        "ip_address": "%s/%s",
                                                        "mac_address": "%s",
                                                        "name": "%s",
                                                        "mtu": %s
                                                },
                                                ''' % (gateway, ip_add, mask, mac_address, int_name, cluster_dict[clus]["mtu"])
                        else:
                        	single_server_string = single_server_string + '''
							{
								"default_gateway": "%s",
								"dhcp": false,
								"ip_address": "%s/%s",
								"mac_address": "%s",
								"name": "%s"
							},
							''' % (gateway, ip_add, mask, mac_address, int_name)
                    else:
			if "mtu" in cluster_dict[clus]:
                                single_server_string = single_server_string + '''
                                        {
                                                        "default_gateway": "%s",
                                                        "dhcp": false,
                                                        "ip_address": "%s/%s",
                                                        "mac_address": "%s",
                                                        "name": "%s",
                                                        "mtu": %s
                                                }
                                                ''' % (gateway, ip_add, mask, mac_address, int_name, cluster_dict[clus]["mtu"])
                        else:
                        	single_server_string = single_server_string + '''
	                                		{
	                                        		"default_gateway": "%s",
	                                        		"dhcp": false,
	                                        		"ip_address": "%s/%s",
	                                        		"mac_address": "%s",
	                                        		"name": "%s"
	                                		}
	                                		''' % (gateway, ip_add, mask, mac_address, int_name)
                    total_server_interfaces = total_server_interfaces - 1
                single_server_string = single_server_string + "],"
                single_server_string = single_server_string + \
                    '\n			"management_interface": "%s"\n' % (
                        cluster_dict[clus]["management_interface"])
                server_json_string = server_json_string + single_server_string
                server_json_string_contd = '''
				},
				"password": "%s",
				"roles": [
				''' % (cluster_dict[clus]["server_password"])
                roles_string = ''
                total_number_of_roles = len(server_dict[clus][i]["roles"])
                for j in server_dict[clus][i]["roles"]:
                    if total_number_of_roles > 1:
                        roles_string = roles_string + '	"%s",\n' % j
                    else:
                        roles_string = roles_string + ' "%s"\n' % j
                    total_number_of_roles = total_number_of_roles - 1
                server_json_string = server_json_string + server_json_string_contd
                server_json_string = server_json_string + roles_string
                # print single_server_string
                # Is the number of servers in the input.json is more than one
                # then we need commas in the json after every server dict.
                if total_server_number > 1:
                    server_json_string_contd = '''
					]
					},
					'''
                    total_server_number = total_server_number - 1
                else:
                    server_json_string_contd = '''
	                        	]
	                        	}
	                        	'''
                # Reduce the number of the total servers by one so that when we
                # insert the last server dict in the json file, it will not
                # include the comma (,) at the end
                server_json_string = server_json_string + server_json_string_contd
        closing_string = '''
		]
	}
		'''
        server_json_string = server_json_string + closing_string
        print server_json_string

# Method for Creating Cluster.json for the Server Manager Mainline Build
def create_cluster_json_mainline():
    change_stack_names()
    final_cluster_json_string = '{\n\t"cluster": [\n'
    number_of_clusters = len(cluster_dict)
    for clus in cluster_dict:
        final_cluster_json_string = final_cluster_json_string + "\t\t{\n"
        if "cluster_id" in cluster_dict[clus]:
            final_cluster_json_string = final_cluster_json_string + '\t\t"id": "%s",\n' %cluster_dict[clus]["cluster_id"]
        final_cluster_json_string = final_cluster_json_string + '\t\t"parameters":{\n'
        if 'domain' in cluster_dict[clus]['parameters']:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t"domain": "%s",\n' %cluster_dict[clus]["parameters"]['domain']
        for net in network_dict:
            if network_dict[net]['role'] == 'management':
                final_cluster_json_string = final_cluster_json_string + '\t\t\t"gateway": "%s",\n' %network_dict[net]['default_gateway']
                final_cluster_json_string = final_cluster_json_string + '\t\t\t"subnet_mask": "255.255.255.0",\n'
        final_cluster_json_string = final_cluster_json_string + '\t\t\t"provision":{\n'
        if 'contrail_4' in cluster_dict[clus]["parameters"]["provision"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t"contrail_4": {\n'
            if "docker_registry" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"docker_registry": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["docker_registry"]
            if "api_server_ssl" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"apiserver_auth_protocol": "https",\n'
            if "docker_registry_insecure" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"docker_registry_insecure": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["docker_registry_insecure"]
            if "controller_image" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"controller_image": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["controller_image"]
            if "analytics_image" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"analytics_image": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["analytics_image"]
            if "lb_image" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"lb_image": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["lb_image"]
            if "analyticsdb_image" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"analyticsdb_image": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["analyticsdb_image"]
            if "agent_image" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"agent_image": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["agent_image"]
            if "ssl_certs_src_dir" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"ssl_certs_src_dir": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["ssl_certs_src_dir"]
            if "tor_ca_cert_file" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"tor_ca_cert_file": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["tor_ca_cert_file"]
            if "tor_ssl_certs_src_dir" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"tor_ssl_certs_src_dir": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["tor_ssl_certs_src_dir"]
            if "ctrl_data_network" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"ctrl_data_network": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["ctrl_data_network"]
            if "enable_lbaas" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"enable_lbaas": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["enable_lbaas"]
            if "tsn_mode" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"tsn_mode": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["tsn_mode"]
            if "rbac" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                if cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["rbac"] == 'true':
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"api_config":{\n'
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"log_level": "SYS_NOTICE",\n'
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"aaa_mode": "rbac"\n'
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t},\n'
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"analytics_api_config":{\n'
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"log_level": "SYS_NOTICE",\n'
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"log": "/var/log/contrail/contrail-analytics-api.log",\n'
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"aaa_mode": "rbac"\n'
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t},\n'
            if "global_config" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"global_config": {\n'
                if "cloud_orchestrator" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]:
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"cloud_orchestrator": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["cloud_orchestrator"]
                if "external_lb" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]:
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"external_lb": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["external_lb"]
                if "external_rabbitmq_servers" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]:
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"external_rabbitmq_servers": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["external_rabbitmq_servers"]
                if "external_zookeeper_servers" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]:
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"external_zookeeper_servers": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["external_zookeeper_servers"]
                if "external_cassandra_servers" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]:
                    final_cluster_json_string =  final_cluster_json_string + '\t\t\t\t\t\t"external_cassandra_servers": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["external_cassandra_servers"]
                if "external_configdb_servers" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]:
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"external_configdb_servers": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["external_configdb_servers"]
                if "xmpp_auth_ssl" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]:
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"xmpp_auth_enable": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["xmpp_auth_ssl"]
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"xmpp_dns_auth_enable": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["xmpp_auth_ssl"]
                if "sandesh_ssl" in cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]:
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"sandesh_ssl_enable": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["contrail_4"]["global_config"]["sandesh_ssl"]
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"log_level": "SYS_INFO"\n'
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t}\n'
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t},\n'
        # Contrail Part of the cluster.json
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t"contrail": {\n'
        if "kernel_upgrade" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"kernel_upgrade": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["contrail"]["kernel_upgrade"]
        for server in server_dict[clus]:
            if "contrail-lb" in server_dict[clus][server]["roles"]:
                lb_external = ''
                lb_internal = ''
                for n in server_dict[clus][server]["ip_address"]:
                    if network_dict[n]["role"] == "management":
                        lb_external = server_dict[clus][server]["ip_address"][n]
                    if network_dict[n]["role"] == "control-data":
                        lb_internal = server_dict[clus][server]["ip_address"][n]
                if len(lb_external) != 0:
                    final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"ha": {\n'
                    if len(lb_internal) != 0:
                        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"contrail_external_vip": "%s",\n' % lb_external
                        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"contrail_internal_vip": "%s"\n' % lb_internal
                        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t},\n'
                    else:
                        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"contrail_external_vip": "%s"\n' % lb_external
                        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t},\n'
        config_node_control_data_ip_list = []
        for server in server_dict[clus]:
            if "contrail-controller" in server_dict[clus][server]["roles"]:
                if len(server_dict[clus][server]["ip_address"]) == 1:
                    for temp in server_dict[clus][server]["ip_address"]:
                        config_node_control_data_ip_list.append(str(server_dict[clus][server]["ip_address"][temp]))
                else:
                    for temp in server_dict[clus][server]["ip_address"]:
                        if network_dict[temp]["role"] == "control-data":
                            config_node_control_data_ip_list.append(str(server_dict[clus][server]["ip_address"][temp]))
        config_ip_list_string = '[ '
        ip_tot = len(config_node_control_data_ip_list)
        for ip in config_node_control_data_ip_list:
            if ip_tot > 1:
                config_ip_list_string = config_ip_list_string + '"%s", ' % ip
            else:
                config_ip_list_string = config_ip_list_string + '"%s" ' % ip
            ip_tot = ip_tot - 1
        config_ip_list_string = config_ip_list_string + ']'
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"config": {\n'
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"config_ip_list": %s,\n' % config_ip_list_string
        if "manage_neutron" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"manage_neutron": %s\n' % cluster_dict[clus]["parameters"]["provision"]["contrail"]["manage_neutron"]
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t}\n'
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t},\n'

        # Kolla Globals part of the cluster.json
        if "kolla_globals" in cluster_dict[clus]["parameters"]["provision"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t"kolla_globals": {\n'
            if "kolla_base_distro" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"kolla_base_distro" :"%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["kolla_base_distro"]
            if "openstack_release" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"openstack_release": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["openstack_release"]
            if "enable_nova_compute" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"enable_nova_compute": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["enable_nova_compute"]
            if "keystone_admin_user" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"keystone_admin_user": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["keystone_admin_user"]
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"keystone_admin_url": "{{ admin_protocol }}://{{ kolla_internal_fqdn }}:{{ keystone_admin_port }}",\n'
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"keystone_internal_url": "{{ internal_protocol }}://{{ kolla_internal_fqdn }}:{{ keystone_public_port }}",\n'
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"keystone_public_url": "{{ public_protocol }}://{{ kolla_external_fqdn }}:{{ keystone_public_port }}",\n'
            if "kolla_internal_vip_address" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"kolla_internal_vip_address": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["kolla_internal_vip_address"]
            if "network_interface" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"network_interface": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["network_interface"]
            if "kolla_external_vip_address" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"kolla_external_vip_address": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["kolla_external_vip_address"]
            if "kolla_external_vip_interface" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"kolla_external_vip_interface": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["kolla_external_vip_interface"]
            if "neutron_external_interface" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"neutron_external_interface": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["neutron_external_interface"]
            if "neutron_plugin_agent" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"neutron_plugin_agent": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["neutron_plugin_agent"]
            if "enable_neutron_opencontrail" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"enable_neutron_opencontrail": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["enable_neutron_opencontrail"]
            if "keepalived_virtual_router_id" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"keepalived_virtual_router_id": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["keepalived_virtual_router_id"]
            if "contrail_api_interface_address" in cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]:
                final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"contrail_api_interface_address": "%s",\n' %cluster_dict[clus]["parameters"]["provision"]["kolla_globals"]["contrail_api_interface_address"]
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"haproxy_password": "c0ntrail123",\n'
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"keepalived_password": "c0ntrail123"\n'
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t},\n'

        # Openstack part of the cluster.json
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t"openstack": {\n'
        if "external_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            if "internal_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
                openstack_ha_string = '\t\t\t\t\t"ha": {\n'
                openstack_ha_string = openstack_ha_string + '\t\t\t\t\t\t"external_vip": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["external_vip"]
                openstack_ha_string = openstack_ha_string + '\t\t\t\t\t\t"external_virtual_router_id": 101,\n'
                openstack_ha_string = openstack_ha_string + '\t\t\t\t\t\t"internal_virtual_router_id": 102,\n'
                openstack_ha_string = openstack_ha_string + '\t\t\t\t\t\t"internal_vip": "%s"\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["internal_vip"]
                openstack_ha_string = openstack_ha_string + "\t\t\t\t\t},\n"
            else:
                openstack_ha_string = '\t\t\t\t\t"ha": {\n'
                openstack_ha_string = openstack_ha_string + '\t\t\t\t\t\t"external_vip": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["external_vip"]
                openstack_ha_string = openstack_ha_string + '\t\t\t\t\t\t"external_virtual_router_id": 101\n' 
                openstack_ha_string = openstack_ha_string + "\t\t\t\t\t},\n"
            final_cluster_json_string =  final_cluster_json_string + openstack_ha_string
        if "openstack_manage_amqp" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"openstack_manage_amqp": %s,\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["openstack_manage_amqp"]
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t"keystone": {\n'
        if "keystone_version" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"version": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["keystone_version"]
        if "keystone_auth_protocol" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"auth_protocol": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["keystone_auth_protocol"]
        else:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"auth_protocol": "http",\n'
        if "keystone_admin_token" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"admin_token": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["keystone_admin_token"]
        else:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"admin_token": "c0ntrail123",\n'
        if "keystone_ip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"ip": "%s",\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["keystone_ip"]
        if "keystone_admin_password" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"admin_password": "%s"\n' % cluster_dict[clus]["parameters"]["provision"]["openstack"]["keystone_admin_password"]
        else:
            final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t\t"admin_password": "c0ntrail123"\n'
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t\t}\n'
        final_cluster_json_string = final_cluster_json_string + '\t\t\t\t}\n'
        final_cluster_json_string = final_cluster_json_string + '\t\t\t}\n'
        final_cluster_json_string = final_cluster_json_string + '\t\t}\n'
        number_of_clusters = number_of_clusters - 1
        if number_of_clusters > 0:
            final_cluster_json_string = final_cluster_json_string + '\t},\n'
        else:
            final_cluster_json_string = final_cluster_json_string + '\t}\n'
    final_cluster_json_string = final_cluster_json_string + '\t]\n'
    final_cluster_json_string = final_cluster_json_string + '}\n'
    print final_cluster_json_string


# Method for creating cluster json for the server manager


def create_cluster_json():
    change_stack_names()
    clus_json_string = '{\n\t"cluster":[\n'
    no_of_clusters = len(cluster_dict)
    for clus in cluster_dict:
        individual_clus_string = '\t\t{\n'
        if "cluster_id" in cluster_dict[clus]:
            individual_clus_string = individual_clus_string + \
                '\t\t"id": "%s",\n' % cluster_dict[clus]["cluster_id"]
        individual_clus_string = individual_clus_string + \
            '\t\t"parameters":{\n'
        if "domain" in cluster_dict[clus]["parameters"]:
            individual_clus_string = individual_clus_string + \
                '\t\t\t"domain": "%s",\n' % cluster_dict[clus]["parameters"]["domain"]
        individual_clus_string = individual_clus_string + \
            '\t\t\t"provision":{\n'
        # Lets start the contrail Part
        individual_clus_string = individual_clus_string + \
            '\t\t\t\t"contrail":{\n'
        if "enable_lbaas" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
	    individual_clus_string = individual_clus_string + \
		'\t\t\t\t\t"enable_lbaas": %s,\n' % cluster_dict[clus][
		    "parameters"]["provision"]["contrail"]["enable_lbaas"]
	if "minimum_disk_database" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
            individual_clus_string = individual_clus_string + \
                '\t\t\t\t\t"database":{\n'
            individual_clus_string = individual_clus_string + \
                '\t\t\t\t\t\t"minimum_diskGB": %d\n' % cluster_dict[clus][
                    "parameters"]["provision"]["contrail"]["minimum_disk_database"]
            individual_clus_string = individual_clus_string + '\t\t\t\t\t},\n'
        if "enable_rabbitmq_ssl" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
            individual_clus_string = individual_clus_string + \
                '\t\t\t\t\t"amqp_ssl":"%s",\n' % cluster_dict[clus][
                    "parameters"]["provision"]["contrail"]["enable_rabbitmq_ssl"]
        if "xmpp_auth_ssl" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
	    individual_clus_string = individual_clus_string + \
		'\t\t\t\t\t"xmpp_auth_enable":"%s",\n' % cluster_dict[clus][
		    "parameters"]["provision"]["contrail"]["xmpp_auth_ssl"]
	    individual_clus_string = individual_clus_string + \
		'\t\t\t\t\t"xmpp_dns_auth_enable":"%s",\n' % cluster_dict[clus][
		    "parameters"]["provision"]["contrail"]["xmpp_auth_ssl"]
	if "kernel_version" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
            individual_clus_string = individual_clus_string + \
                '\t\t\t\t\t"kernel_version":"%s",\n' % cluster_dict[clus][
                    "parameters"]["provision"]["contrail"]["kernel_version"]
        if "kernel_upgrade" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
            individual_clus_string = individual_clus_string + \
                '\t\t\t\t\t"kernel_upgrade": %s' % cluster_dict[clus][
                    "parameters"]["provision"]["contrail"]["kernel_upgrade"]
        # Contrail Part Ends here
        individual_clus_string = individual_clus_string + '\t\t\t\t},\n'

        # Now Lets start the openstack part
        individual_clus_string = individual_clus_string + \
            '\t\t\t\t"openstack":{\n'
	if "openstack_manage_amqp" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
	    individual_clus_string = individual_clus_string + \
		'\t\t\t\t\t"openstack_manage_amqp":"%s",\n' % cluster_dict[clus][
		    "parameters"]["provision"]["openstack"]["openstack_manage_amqp"] 
        if "keystone_admin_password" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            individual_clus_string = individual_clus_string + \
                '\t\t\t\t\t"keystone":{\n'
            individual_clus_string = individual_clus_string + \
                '\t\t\t\t\t\t"admin_password": "%s",\n' % cluster_dict[clus][
                    "parameters"]["provision"]["openstack"]["keystone_admin_password"]
            #individual_clus_string = individual_clus_string + '},\n'
	if "keystone_ssl" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
	    individual_clus_string = individual_clus_string + \
		'\t\t\t\t\t\t"auth_protocol": "https", \n'
	if "keystone_version" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
	    individual_clus_string = individual_clus_string + \
		'\t\t\t\t\t\t"version": "%s"\n' % cluster_dict[clus][
		    "parameters"]["provision"]["openstack"]["keystone_version"] 
        if (("external_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and (
                "internal_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"])):
            vip_string = ""
            individual_clus_string = individual_clus_string + '\t\t\t\t},\n'
            vip_string = vip_string + '\t\t\t\t"ha":{\n'
            vip_string = vip_string + \
                '\t\t\t\t\t"external_vip": "%s",\n' % cluster_dict[clus][
                    "parameters"]["provision"]["openstack"]["external_vip"]
            vip_string = vip_string + \
                '\t\t\t\t\t"internal_vip": "%s",\n' % cluster_dict[clus][
                    "parameters"]["provision"]["openstack"]["internal_vip"]
            vip_string = vip_string + \
                '\t\t\t\t\t"external_virtual_router_id" : %d,\n' % cluster_dict[clus][
                    "parameters"]["provision"]["openstack"]["external_virtual_router_id"]
            vip_string = vip_string + \
                '\t\t\t\t\t"internal_virtual_router_id" : %d\n' % cluster_dict[clus][
                    "parameters"]["provision"]["openstack"]["internal_virtual_router_id"]
            vip_string = vip_string + '\t\t\t\t}\n'
            vip_string = vip_string + '\t\t\t}\n'
            vip_string = vip_string + '\t\t}\n'
            vip_string = vip_string + '\t}\n'
            no_of_clusters = no_of_clusters - 1
            if no_of_clusters == 0:
                vip_string = vip_string + '}\n'
            else:
                vip_string = vip_string + '},\n'
            individual_clus_string = individual_clus_string + vip_string
        else:
            individual_clus_string = individual_clus_string + '\t\t\t\t}\n'
            individual_clus_string = individual_clus_string + '\t\t\t}\n'
            individual_clus_string = individual_clus_string + '\t\t}\n'
            individual_clus_string = individual_clus_string + '\t}\n'
            no_of_clusters = no_of_clusters - 1
            if no_of_clusters == 0:
                individual_clus_string = individual_clus_string + '}\n'
            else:
                individual_clus_string = individual_clus_string + '},\n'
        clus_json_string = clus_json_string + individual_clus_string
    clus_json_string = clus_json_string + '\t]\n'
    clus_json_string = clus_json_string + '}'
    print clus_json_string


def create_testbedpy_file():
    dict_of_testbed_files = {}
    for clus in testbed_py_dict:
        file_str = ""
        file_str = file_str + "from fabric.api import env \nimport os\n\next_routers = []\n"
        if "router_asn" in testbed_py_dict[clus]:
            file_str = file_str + \
                "router_asn = %s\n\n" % testbed_py_dict[clus]["router_asn"]
        else:
            file_str = file_str + "router_asn = 64512\n\n"
        itr = 1
        if "public_vn_rtgt" in testbed_py_dict[clus]:
            file_str = file_str + \
                "public_vn_rtgt = %s\n\n" % testbed_py_dict[clus]["public_vn_rtgt"]
        if "public_vn_subnet" in testbed_py_dict[clus]:
            file_str = file_str + \
                'public_vn_subnet = "%s"\n\n' % testbed_py_dict[clus]["public_vn_subnet"]
        # hostname_string contains the hostanme of all the servers. This would
        # be added to the main string after wards
        hostname_string = "     'all' : [ "
        build_ip = ""
        control_data_string = "control_data = {\n"
        name_mapping = {}
        if "env_password" in testbed_py_dict[clus]:
            env_password_string = "\nenv.passwords = {\n"
        if "env_ostypes" in testbed_py_dict[clus]:
            env_ostypes_string = "env.ostypes = {\n"
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                for j in server_dict[clus][i]["ip_address"]:
                    if network_dict[j]["role"] == "management":
                        if "config" in server_dict[clus][i]["roles"]:
                            # Build Ip that will be used in the testbed.py file
                            if "host_build" in testbed_py_dict[clus]:
                                build_ip = testbed_py_dict[clus]["host_build"]
                            else:
                                if server_dict[clus][i]["floating_ip"] == 'true':
                                    fip_dict_1 = get_all_fip_dict()
                                    build_ip = '%s' % fip_dict_1[(server_dict[clus][i]["name"])]
                                else:
                                    build_ip = server_dict[clus][i]["ip_address"][j]
                        manag_ip = server_dict[clus][i]["ip_address"][j]
                    else:
                        if network_dict[j]["role"] == "control-data":
                            # control data ip that will be used in the
                            # control-data section of the testbed.py file
                            control_ip = server_dict[clus][i]["ip_address"][j]
                            gateway = network_dict[j]["default_gateway"]
                        else:
                            continue
                for net in network_dict:
                    if network_dict[net]["role"] == 'control-data':
                        if "control_data_vlan" in testbed_py_dict[clus]:
                            control_data_string = control_data_string + "   host%s : { 'ip': '%s', 'gw' : '%s', 'device': 'eth1', 'vlan': '%s'},\n" % (
                                str(itr), control_ip, gateway, testbed_py_dict[clus]["control_data_vlan"])
                        else:
                            control_data_string = control_data_string + \
                                "   host%s : { 'ip': '%s', 'gw' : '%s', 'device': 'eth1'},\n" % (
                                    str(itr), control_ip, gateway)
                if server_dict[clus][i]["floating_ip"] == 'true':
                    fip_dict_1 = get_all_fip_dict()
                    file_str = file_str + \
                        "host%s = 'root@%s'\n" % (str(itr), fip_dict_1[(server_dict[clus][i]["name"])])
                else:    
                    file_str = file_str + \
                        "host%s = 'root@%s'\n" % (str(itr), manag_ip)
                if "env_password" in testbed_py_dict[clus]:
                    env_password_string = env_password_string + \
                        "   host%s: '%s',\n" % (
                            str(itr), testbed_py_dict[clus]["env_password"])
                if "env_ostypes" in testbed_py_dict[clus]:
                    env_ostypes_string = env_ostypes_string + \
                        "     host%s: '%s',\n" % (
                            str(itr), testbed_py_dict[clus]["env_ostypes"])
                # logic for not adding ',' (comma) after the last hostname in
                # the env.hostname field of the testbed.py being created.
                if itr == len(server_dict[clus]) - 1:
                    hostname_string = hostname_string + "'" + \
                        (server_dict[clus][i]["name"]) + "' "
                    testbed_py_name = "host%s" % str(itr)
                    name_mapping[server_dict[clus][i]
                                 ["name"]] = testbed_py_name
                else:
                    hostname_string = hostname_string + "'" + \
                        (server_dict[clus][i]["name"]) + "', "
                    testbed_py_name = "host%s" % str(itr)
                    name_mapping[server_dict[clus][i]
                                 ["name"]] = testbed_py_name
                itr += 1
        hostname_string = hostname_string + "]\n"
        control_data_string = control_data_string + "}\n\n"
        role_per_server_mapping = {
            "all": [],
            "cfgm": [],
            "openstack": [],
            "webui": [],
            "control": [],
            "collector": [],
            "database": [],
            "compute": [],
            "build": ["host_build"]}
        if "env_ostypes" in testbed_py_dict[clus]:
            env_ostypes_string = env_ostypes_string + "}\n\n"
        if "env_password" in testbed_py_dict[clus]:
            env_password_string = env_password_string + \
                "   host_build: '%s',\n}\n\n" % testbed_py_dict[clus]["env_password"]
            file_str = file_str + \
                "\nenv.password = '%s'\n" % testbed_py_dict[clus]["env_password"]
        file_str = file_str + "host_build = 'root@%s'\n\n" % build_ip
        # Lets Get the role definitions for all the servers in the input file
        # All the hostnames for env.roles section in testbed.py file
        all_host_list = name_mapping.values()
        for i in all_host_list:
            role_per_server_mapping["all"].append(i)
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                if "config" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["cfgm"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "openstack" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["openstack"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "webui" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["webui"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "control" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["control"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "collector" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["collector"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "database" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["database"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "compute" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["compute"].append(
                        name_mapping[server_dict[clus][i]["name"]])
        file_str = file_str + "env.hostnames = {\n"
        file_str = file_str + hostname_string + "}\n\n"
        file_str = file_str + "env.interface_rename = False\n\n"
        for net in network_dict:
            if network_dict[net]["role"] == "control-data":
                file_str = file_str + control_data_string
        # Print all the role defs referenced from the 'role_per_server_mapping'
        # dict mention above
        file_str = file_str + "env.roledefs = {\n"
        #itr = len(role_per_server_mapping)
        itr = 1
        for i in role_per_server_mapping:
            #inner_iter = len(role_per_server_mapping[i])
            inner_iter = 1
            file_str = file_str + "	'%s' : [ " % i
            for j in role_per_server_mapping[i]:
                if inner_iter == len(role_per_server_mapping[i]):
                    file_str = file_str + j + " ]"
                else:
                    file_str = file_str + "%s, " % j
                inner_iter += 1
            if itr == len(role_per_server_mapping):
                file_str = file_str + "\n"
            else:
                file_str = file_str + ",\n"
            itr += 1
        file_str = file_str + "}\n\n"
        if "openstack_admin_password" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.openstack_admin_password = '%s'\n\n" % testbed_py_dict[
                    clus]["openstack_admin_password"]
        all_fip_dict = get_all_fip_dict()
        file_str = file_str + "env.all_server_fips = %s\n" % all_fip_dict
        if "env.log_scenario" in testbed_py_dict[clus]:
            log_scenario_str = ''
            if "auth_protocol" in testbed_py_dict[clus]["env.log_scenario"]:
                if testbed_py_dict[clus]["env.log_scenario"]["auth_protocol"] == "https":
                    if "keystone_version" in testbed_py_dict[clus]["env.log_scenario"]:
                        if testbed_py_dict[clus]["env.log_scenario"]["keystone_version"] == "v3":
                            if "description" in testbed_py_dict[clus]["env.log_scenario"]:
                                log_scenario_str = log_scenario_str + \
                                    "env.log_scenario= %s\n" % testbed_py_dict[
                                        clus]["env.log_scenario"]["description"]
                            log_scenario_str = log_scenario_str + \
                                "env.keystone = {\n"
                            log_scenario_str = log_scenario_str + "	'version': 'v3',\n"
                            log_scenario_str = log_scenario_str + "	'auth_protocol': 'https'\n"
                            log_scenario_str = log_scenario_str + "}\n"
                    else:
                        if "description" in testbed_py_dict[clus]["env.log_scenario"]:
                            log_scenario_str = log_scenario_str + \
                                "env.log_scenario= %s\n" % testbed_py_dict[
                                    clus]["env.log_scenario"]["description"]
                        log_scenario_str = log_scenario_str + \
                            "env.keystone = {\n"
                        log_scenario_str = log_scenario_str + "	'auth_protocol': 'https'\n"
                        log_scenario_str = log_scenario_str + "}\n"
                    log_scenario_str = log_scenario_str + "env.cfgm = {\n"
                    log_scenario_str = log_scenario_str + "	'auth_protocol': 'https'\n"
                    log_scenario_str = log_scenario_str + "}\n"
                else:
                    if "description" in testbed_py_dict[clus]["env.log_scenario"]:
                        log_scenario_str = log_scenario_str + \
                            "env.log_scenario= %s\n" % testbed_py_dict[clus]["env.log_scenario"]["description"]
                    else:
                        pass
                file_str = file_str + log_scenario_str
        if "enable_rbac" in testbed_py_dict[clus]:
            if testbed_py_dict[clus]["enable_rbac"] == "true":
                file_str = file_str + "cloud_admin_role = 'admin'\n"
                file_str = file_str + "aaa_mode = 'rbac'\n"
        if "env_password" in testbed_py_dict[clus]:
            file_str = file_str + env_password_string
        if "env_ostypes" in testbed_py_dict[clus]:
            file_str = file_str + env_ostypes_string
        if (("external_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and (
                "internal_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"])):
            file_str = file_str + "ha_setup = True\n"
            file_str = file_str + "env.ha = {\n"
            file_str = file_str + \
                "	'internal_vip' : '%s',\n" % cluster_dict[clus][
                    "parameters"]["provision"]["openstack"]["internal_vip"]
            if "contrail_internal_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
                file_str = file_str + \
                    "	'contrail_internal_vip' : '%s',\n" % cluster_dict[clus][
                        "parameters"]["provision"]["contrail"]["contrail_internal_vip"]
            if "contrail_internal_virtual_router_id" in cluster_dict[
                    clus]["parameters"]["provision"]["contrail"]:
                file_str = file_str + \
                    "	'contrail_internal_virtual_router_id' : %s,\n" % cluster_dict[clus][
                        "parameters"]["provision"]["contrail"]["contrail_internal_virtual_router_id"]
            if "contrail_external_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
                file_str = file_str + \
                    "	'contrail_external_vip' : '%s',\n" % cluster_dict[clus][
                        "parameters"]["provision"]["contrail"]["contrail_external_vip"]
            if "contrail_external_virtual_router_id" in cluster_dict[
                    clus]["parameters"]["provision"]["contrail"]:
                file_str = file_str + \
                    "	'contrail_external_virtual_router_id' : %s,\n" % cluster_dict[clus][
                        "parameters"]["provision"]["contrail"]["contrail_external_virtual_router_id"]
            file_str = file_str + \
                "	'external_vip' : '%s'\n}\n\n" % cluster_dict[clus][
                    "parameters"]["provision"]["openstack"]["external_vip"]
        if "ipmi_username" in testbed_py_dict[clus]:
            file_str = file_str + \
                "ipmi_username = '%s'\n" % testbed_py_dict[clus]["ipmi_username"]
        if "ipmi_password" in testbed_py_dict[clus]:
            file_str = file_str + \
                "ipmi_password = '%s'\n\n" % testbed_py_dict[clus]["ipmi_password"]
        file_str = file_str + \
            "env.cluster_id='%s'\n" % cluster_dict[clus]["cluster_id"]
        if "minimum_diskGB" in testbed_py_dict[clus]:
            file_str = file_str + \
                "minimum_diskGB = %d\n" % testbed_py_dict[clus]["minimum_diskGB"]
        if "env.test_repo_dir" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.test_repo_dir= '%s'\n" % testbed_py_dict[clus]["env.test_repo_dir"]
        if "env.mail_from" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mail_from= '%s'\n" % testbed_py_dict[clus]["env.mail_from"]
        if "env.mail_to" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mail_to= '%s'\n" % testbed_py_dict[clus]["env.mail_to"]
        if "env.mail_server" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mail_server = '%s'\n" % testbed_py_dict[clus]["env.mail_server"]
        if "env.mail_port" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mail_port = '%s'\n" % testbed_py_dict[clus]["env.mail_port"]
        if "multi_tenancy" in testbed_py_dict[clus]:
            file_str = file_str + \
                "multi_tenancy= %s\n" % testbed_py_dict[clus]["multi_tenancy"]
        if "env.interface_rename" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.interface_rename = %s\n" % testbed_py_dict[clus]["env.interface_rename"]
        if "env.encap_priority" in testbed_py_dict[clus]:
            file_str = file_str + \
                'env.encap_priority = "%s"\n' % testbed_py_dict[clus]["env.encap_priority"]
        if "env.enable_lbaas" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.enable_lbaas = %s\n" % testbed_py_dict[clus]["env.enable_lbaas"]
        if "enable_ceilometer" in testbed_py_dict[clus]:
            file_str = file_str + \
                "enable_ceilometer = %s\n" % testbed_py_dict[clus]["enable_ceilometer"]
        if "ceilometer_polling_interval" in testbed_py_dict[clus]:
            file_str = file_str + \
                "ceilometer_polling_interval = %d\n" % testbed_py_dict[
                    clus]["ceilometer_polling_interval"]
        if "do_parallel" in testbed_py_dict[clus]:
            file_str = file_str + \
                "do_parallel = %s\n" % testbed_py_dict[clus]["do_parallel"]
        if "env.image_web_server" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.image_web_server = '%s'\n" % testbed_py_dict[clus]["env.image_web_server"]
        if "env.testbed_location" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.testbed_location = '%s'\n" % testbed_py_dict[clus]["env.testbed_location"]
        if "env.mx_gw_test" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mx_gw_test = %s\n" % testbed_py_dict[clus]["env.mx_gw_test"]
        if "env.ntp_server" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.ntp_server = '%s'\n" % testbed_py_dict[clus]["env.ntp_server"]
        if "env.rsyslog_params" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.rsyslog_params = %s\n" % testbed_py_dict[clus]["env.rsyslog_params"]
        if "storage_replica_size" in testbed_py_dict[clus]:
            file_str = file_str + \
                "storage_replica_size = %s\n" % testbed_py_dict[clus]["storage_replica_size"]

        dict_of_testbed_files[clus] = file_str
    for testbed in dict_of_testbed_files:
        print dict_of_testbed_files[testbed]

# Method to create testbed.py file for the mainline build


def create_testbedpy_file_mainline():
    dict_of_testbed_files = {}
    for clus in testbed_py_dict:
        file_str = ""
        file_str = file_str + "from fabric.api import env \nimport os\n\next_routers = []\n"
        if "router_asn" in testbed_py_dict[clus]:
            file_str = file_str + \
                "router_asn = %s\n\n" % testbed_py_dict[clus]["router_asn"]
        else:
            file_str = file_str + "router_asn = 64512\n\n"
        itr = 1
        if "public_vn_rtgt" in testbed_py_dict[clus]:
            file_str = file_str + \
                "public_vn_rtgt = %s\n\n" % testbed_py_dict[clus]["public_vn_rtgt"]
        if "public_vn_subnet" in testbed_py_dict[clus]:
            file_str = file_str + \
                'public_vn_subnet = "%s"\n\n' % testbed_py_dict[clus]["public_vn_subnet"]
        # hostname_string contains the hostanme of all the servers. This would
        # be added to the main string after wards
        hostname_string = "     'all' : [ "
        build_ip = ""
        control_data_string = "control_data = {\n"
        name_mapping = {}
        if "env_password" in testbed_py_dict[clus]:
            env_password_string = "\nenv.passwords = {\n"
        if "env_ostypes" in testbed_py_dict[clus]:
            env_ostypes_string = "env.ostypes = {\n"
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                for j in server_dict[clus][i]["ip_address"]:
                    if network_dict[j]["role"] == "management":
                        if "contrail-controller" in server_dict[clus][i]["roles"]:
                            # Build Ip that will be used in the testbed.py file
                            if "host_build" in testbed_py_dict[clus]:
                                build_ip = testbed_py_dict[clus]["host_build"]
                            else:
                                if server_dict[clus][i]["floating_ip"] == 'true':
                                    fip_dict_1 = get_all_fip_dict()
                                    #print fip_dict_1
                                    build_ip = '%s' % fip_dict_1[(server_dict[clus][i]["name"])]
                                else:
                                    build_ip = server_dict[clus][i]["ip_address"][j]
                        manag_ip = server_dict[clus][i]["ip_address"][j]
                    else:
                        if network_dict[j]["role"] == "control-data":
                            # control data ip that will be used in the
                            # control-data section of the testbed.py file
                            control_ip = server_dict[clus][i]["ip_address"][j]
                            gateway = network_dict[j]["default_gateway"]
                        else:
                            continue
                for net in network_dict:
                    if network_dict[net]["role"] == 'control-data':
                        if "control_data_vlan" in testbed_py_dict[clus]:
                            control_data_string = control_data_string + "   host%s : { 'ip': '%s', 'gw' : '%s', 'device': 'eth1', 'vlan': '%s'},\n" % (
                                str(itr), control_ip, gateway, testbed_py_dict[clus]["control_data_vlan"])
                        else:
                            control_data_string = control_data_string + \
                                "   host%s : { 'ip': '%s', 'gw' : '%s', 'device': 'eth1'},\n" % (
                                    str(itr), control_ip, gateway)

                if server_dict[clus][i]["floating_ip"] == 'true':
                    fip_dict_1 = get_all_fip_dict()
                    file_str = file_str + \
                        "host%s = 'root@%s'\n" % (str(itr), fip_dict_1[(server_dict[clus][i]["name"])])
                else:    
                    file_str = file_str + \
                        "host%s = 'root@%s'\n" % (str(itr), manag_ip)
                #file_str = file_str + \
                #    "host%s = 'root@%s'\n" % (str(itr), manag_ip)
                if "env_password" in testbed_py_dict[clus]:
                    env_password_string = env_password_string + \
                        "   host%s: '%s',\n" % (
                            str(itr), testbed_py_dict[clus]["env_password"])
                if "env_ostypes" in testbed_py_dict[clus]:
                    env_ostypes_string = env_ostypes_string + \
                        "     host%s: '%s',\n" % (
                            str(itr), testbed_py_dict[clus]["env_ostypes"])
                # logic for not adding ',' (comma) after the last hostname in
                # the env.hostname field of the testbed.py being created.
                if itr == len(server_dict[clus]) - 1:
                    hostname_string = hostname_string + "'" + \
                        (server_dict[clus][i]["name"]) + "' "
                    testbed_py_name = "host%s" % str(itr)
                    name_mapping[server_dict[clus][i]
                                 ["name"]] = testbed_py_name
                else:
                    hostname_string = hostname_string + "'" + \
                        (server_dict[clus][i]["name"]) + "', "
                    testbed_py_name = "host%s" % str(itr)
                    name_mapping[server_dict[clus][i]
                                 ["name"]] = testbed_py_name
                itr += 1
        hostname_string = hostname_string + "]\n"
        control_data_string = control_data_string + "}\n\n"

        testbedfile_serverjson_role_mapping = {
            "openstack": "openstack",
            "contrail-controller": "control",
            "contrail-analytics": "collector",
            "contrail-analyticsdb": "database",
            "contrail-compute": "compute",
            "contrail-lb": "lb",
            "contrail-cfgm": "cfgm"}
        role_per_server_mapping = {
            "all": [],
            "openstack": [],
            "contrail-controller": [],
            "contrail-analytics": [],
            "contrail-analyticsdb": [],
            "contrail-compute": [],
            "build": ["host_build"]}
        if "env_ostypes" in testbed_py_dict[clus]:
            env_ostypes_string = env_ostypes_string + "}\n\n"
        if "env_password" in testbed_py_dict[clus]:
            env_password_string = env_password_string + \
                "   host_build: '%s',\n}\n\n" % testbed_py_dict[clus]["env_password"]
            file_str = file_str + \
                "\nenv.password = '%s'\n" % testbed_py_dict[clus]["env_password"]
        file_str = file_str + "host_build = 'root@%s'\n\n" % build_ip
        # Lets Get the role definitions for all the servers in the input file
        # All the hostnames for env.roles section in testbed.py file
        all_host_list = name_mapping.values()
        for i in all_host_list:
            role_per_server_mapping["all"].append(i)
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                if "openstack" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["openstack"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "contrail-controller" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["contrail-controller"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                    if "contrail-cfgm" in role_per_server_mapping:
                        role_per_server_mapping["contrail-cfgm"].append(
                            name_mapping[server_dict[clus][i]["name"]])
                    else:
                        role_per_server_mapping["contrail-cfgm"] = []
                        role_per_server_mapping["contrail-cfgm"].append(
                            name_mapping[server_dict[clus][i]["name"]])
                if "contrail-analytics" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["contrail-analytics"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "contrail-analyticsdb" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["contrail-analyticsdb"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "contrail-compute" in server_dict[clus][i]["roles"]:
                    role_per_server_mapping["contrail-compute"].append(
                        name_mapping[server_dict[clus][i]["name"]])
                if "contrail-lb" in server_dict[clus][i]["roles"]:
                    if "contrail-lb" in role_per_server_mapping:
                        role_per_server_mapping["contrail-lb"].append(
                            name_mapping[server_dict[clus][i]["name"]])
                    else:
                        role_per_server_mapping["contrail-lb"] = []
                        role_per_server_mapping["contrail-lb"].append(
                            name_mapping[server_dict[clus][i]["name"]])
        file_str = file_str + "env.hostnames = {\n"
        file_str = file_str + hostname_string + "}\n\n"
        file_str = file_str + "env.interface_rename = False\n\n"
        for net in network_dict:
            if network_dict[net]["role"] == "control-data":
                file_str = file_str + control_data_string
        # Print all the role defs referenced from the 'role_per_server_mapping'
        # dict mention above
        file_str = file_str + "env.roledefs = {\n"
        #itr = len(role_per_server_mapping)
        itr = 1
        for i in role_per_server_mapping:
            #inner_iter = len(role_per_server_mapping[i])
            inner_iter = 1
            if i not in testbedfile_serverjson_role_mapping:
                file_str = file_str + "\t'%s' : [ " % i
            else:
                file_str = file_str + \
                    "\t'%s' : [ " % testbedfile_serverjson_role_mapping[i]
            for j in role_per_server_mapping[i]:
                if inner_iter == len(role_per_server_mapping[i]):
                    file_str = file_str + j + " ]"
                else:
                    file_str = file_str + "%s, " % j
                inner_iter += 1
            if itr == len(role_per_server_mapping):
                file_str = file_str + "\n"
            else:
                file_str = file_str + ",\n"
            itr += 1
        file_str = file_str + "}\n\n"
        if "openstack_admin_password" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.openstack_admin_password = '%s'\n\n" % testbed_py_dict[
                    clus]["openstack_admin_password"]
        all_fip_dict = get_all_fip_dict()
        file_str = file_str + "env.all_server_fips = %s\n" % all_fip_dict
        if "env.log_scenario" in testbed_py_dict[clus]:
            log_scenario_str = ''
            if "auth_protocol" in testbed_py_dict[clus]["env.log_scenario"]:
                if testbed_py_dict[clus]["env.log_scenario"]["auth_protocol"] == "https":
                    if "keystone_version" in testbed_py_dict[clus]["env.log_scenario"]:
                        if testbed_py_dict[clus]["env.log_scenario"]["keystone_version"] == "v3":
                            if "description" in testbed_py_dict[clus]["env.log_scenario"]:
                                log_scenario_str = log_scenario_str + \
                                    "env.log_scenario= %s\n" % testbed_py_dict[
                                        clus]["env.log_scenario"]["description"]
                            log_scenario_str = log_scenario_str + \
                                "env.keystone = {\n"
                            log_scenario_str = log_scenario_str + "	'version': 'v3',\n"
                            log_scenario_str = log_scenario_str + "	'auth_protocol': 'https'\n"
                            log_scenario_str = log_scenario_str + "}\n"
                    else:
                        if "description" in testbed_py_dict[clus]["env.log_scenario"]:
                            log_scenario_str = log_scenario_str + \
                                "env.log_scenario= %s\n" % testbed_py_dict[
                                    clus]["env.log_scenario"]["description"]
                        log_scenario_str = log_scenario_str + \
                            "env.keystone = {\n"
                        log_scenario_str = log_scenario_str + "	'auth_protocol': 'https'\n"
                        log_scenario_str = log_scenario_str + "}\n"
                    log_scenario_str = log_scenario_str + "env.cfgm = {\n"
                    log_scenario_str = log_scenario_str + "	'auth_protocol': 'https'\n"
                    log_scenario_str = log_scenario_str + "}\n"
                else:
                    if "description" in testbed_py_dict[clus]["env.log_scenario"]:
                        log_scenario_str = log_scenario_str + \
                            "env.log_scenario= %s\n" % testbed_py_dict[clus]["env.log_scenario"]["description"]
                    else:
                        pass
                file_str = file_str + log_scenario_str
        if "enable_rbac" in testbed_py_dict[clus]:
            if testbed_py_dict[clus]["enable_rbac"] == "true":
                file_str = file_str + "cloud_admin_role = 'admin'\n"
                file_str = file_str + "aaa_mode = 'rbac'\n"
        if "env_password" in testbed_py_dict[clus]:
            file_str = file_str + env_password_string
        if "env_ostypes" in testbed_py_dict[clus]:
            file_str = file_str + env_ostypes_string
        for server in server_dict[clus]:
            if "contrail-lb" in server_dict[clus][server]["roles"]:
                lb_external = ''
                lb_internal = ''
                for n in server_dict[clus][server]["ip_address"]:
                    if network_dict[n]["role"] == "management":
                        lb_external = server_dict[clus][server]["ip_address"][n]
                    if network_dict[n]["role"] == "control-data":
                        lb_internal = server_dict[clus][server]["ip_address"][n]

        if (("contrail_external_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"]) and (
                "contrail_internal_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"])):
            file_str = file_str + "ha_setup = True\n"
            file_str = file_str + "env.ha = {\n"
            if "contrail_internal_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
                file_str = file_str + \
                    "   'contrail_internal_vip' : '%s',\n" % lb_internal
            if "contrail_external_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
                file_str = file_str + \
                    "   'contrail_external_vip' : '%s'\n}\n\n" % lb_external
        '''
		if (("external_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"]) and ("internal_vip" in cluster_dict[clus]["parameters"]["provision"]["openstack"])):
			file_str = file_str+"ha_setup = True\n"
			file_str = file_str + "env.ha = {\n"
			file_str = file_str+"	'internal_vip' : '%s',\n"%cluster_dict[clus]["parameters"]["provision"]["openstack"]["internal_vip"]
			if "contrail_internal_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
				file_str = file_str+"	'contrail_internal_vip' : '%s',\n"%cluster_dict[clus]["parameters"]["provision"]["contrail"]["contrail_internal_vip"]
			if "contrail_internal_virtual_router_id" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
				file_str = file_str+"	'contrail_internal_virtual_router_id' : %s,\n"%cluster_dict[clus]["parameters"]["provision"]["contrail"]["contrail_internal_virtual_router_id"]
			if "contrail_external_vip" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
				file_str = file_str+"	'contrail_external_vip' : '%s',\n"%cluster_dict[clus]["parameters"]["provision"]["contrail"]["contrail_external_vip"]
			if "contrail_external_virtual_router_id" in cluster_dict[clus]["parameters"]["provision"]["contrail"]:
				file_str = file_str+"	'contrail_external_virtual_router_id' : %s,\n"%cluster_dict[clus]["parameters"]["provision"]["contrail"]["contrail_external_virtual_router_id"]
			file_str = file_str+"	'external_vip' : '%s'\n}\n\n"%cluster_dict[clus]["parameters"]["provision"]["openstack"]["external_vip"]
		'''
        if "ipmi_username" in testbed_py_dict[clus]:
            file_str = file_str + \
                "ipmi_username = '%s'\n" % testbed_py_dict[clus]["ipmi_username"]
        if "ipmi_password" in testbed_py_dict[clus]:
            file_str = file_str + \
                "ipmi_password = '%s'\n\n" % testbed_py_dict[clus]["ipmi_password"]
	if "openstack_manage_amqp" in cluster_dict[clus]["parameters"]["provision"]["openstack"]:
            if cluster_dict[clus]["parameters"]["provision"]["openstack"]["openstack_manage_amqp"] == "false":
		file_str = file_str + \
		    "env.openstack = {\n"+"    'manage_amqp' : 'no'\n" + "}\n"
        file_str = file_str + \
            "env.cluster_id='%s'\n" % cluster_dict[clus]["cluster_id"]
        if "minimum_diskGB" in testbed_py_dict[clus]:
            file_str = file_str + \
                "minimum_diskGB = %d\n" % testbed_py_dict[clus]["minimum_diskGB"]
        if "env.test_repo_dir" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.test_repo_dir= '%s'\n" % testbed_py_dict[clus]["env.test_repo_dir"]
        if "env.mail_from" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mail_from= '%s'\n" % testbed_py_dict[clus]["env.mail_from"]
        if "env.mail_to" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mail_to= '%s'\n" % testbed_py_dict[clus]["env.mail_to"]
        if "env.mail_server" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mail_server = '%s'\n" % testbed_py_dict[clus]["env.mail_server"]
        if "env.mail_port" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mail_port = '%s'\n" % testbed_py_dict[clus]["env.mail_port"]
        if "multi_tenancy" in testbed_py_dict[clus]:
            file_str = file_str + \
                "multi_tenancy= %s\n" % testbed_py_dict[clus]["multi_tenancy"]
        if "env.interface_rename" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.interface_rename = %s\n" % testbed_py_dict[clus]["env.interface_rename"]
        if "env.encap_priority" in testbed_py_dict[clus]:
            file_str = file_str + \
                'env.encap_priority = "%s"\n' % testbed_py_dict[clus]["env.encap_priority"]
        if "env.enable_lbaas" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.enable_lbaas = %s\n" % testbed_py_dict[clus]["env.enable_lbaas"]
        if "enable_ceilometer" in testbed_py_dict[clus]:
            file_str = file_str + \
                "enable_ceilometer = %s\n" % testbed_py_dict[clus]["enable_ceilometer"]
        if "ceilometer_polling_interval" in testbed_py_dict[clus]:
            file_str = file_str + \
                "ceilometer_polling_interval = %d\n" % testbed_py_dict[
                    clus]["ceilometer_polling_interval"]
        if "do_parallel" in testbed_py_dict[clus]:
            file_str = file_str + \
                "do_parallel = %s\n" % testbed_py_dict[clus]["do_parallel"]
        if "env.image_web_server" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.image_web_server = '%s'\n" % testbed_py_dict[clus]["env.image_web_server"]
        if "env.testbed_location" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.testbed_location = '%s'\n" % testbed_py_dict[clus]["env.testbed_location"]
        if "env.mx_gw_test" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.mx_gw_test = %s\n" % testbed_py_dict[clus]["env.mx_gw_test"]
        if "env.ntp_server" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.ntp_server = '%s'\n" % testbed_py_dict[clus]["env.ntp_server"]
        if "env.rsyslog_params" in testbed_py_dict[clus]:
            file_str = file_str + \
                "env.rsyslog_params = %s\n" % testbed_py_dict[clus]["env.rsyslog_params"]
        if "storage_replica_size" in testbed_py_dict[clus]:
            file_str = file_str + \
                "storage_replica_size = %s\n" % testbed_py_dict[clus]["storage_replica_size"]

        dict_of_testbed_files[clus] = file_str
    for testbed in dict_of_testbed_files:
        print dict_of_testbed_files[testbed]

# Method to get the control data ip with mask so that it can be used in
# server.json required for the mainline build(contrail 4.0 onwards)


def get_control_data_ip_sm():
    ret_ip = ''
    for clus in server_dict:
        for server in server_dict[clus]:
            if server_dict[clus][server]["server_manager"] == "true":
                for i in server_dict[clus][server]["ip_address"]:
                    if len(server_dict[clus][server]["ip_address"]) == 1:
                        ret_ip = server_dict[clus][server]["ip_address"][i]
                        mask_list = network_dict[i]["ip_block_with_mask"].split(
                            '/')
                        ret_ip = ret_ip + '/' + mask_list[1]
                    else:
                        if network_dict[i]["role"] == "control-data":
                            ret_ip = server_dict[clus][server]["ip_address"][i]
                            mask_list = network_dict[i]["ip_block_with_mask"].split(
                                '/')
                            ret_ip = ret_ip + '/' + mask_list[1]
    print ret_ip


def produce_vmx_env_file():
    change_network_dict()
    net_1 = ''
    net_2 = ''
    for i in network_dict:
        if network_dict[i]['role'] == 'management':
            net_1 = network_dict[i]['name']
        else:
            net_2 = network_dict[i]['name']
    # print net_1
    # print net_2
    project_uuid = general_params_dict["project_uuid"]
    undashed_uuid = project_uuid.replace('-', '')
    # print undashed_uuid
    project_name = ''
    a = subprocess.Popen("openstack project list -f json",
                         shell=True, stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp_dict = eval(a_tmp)
    a_tmp = ""
    # print a_tmp_dict
    for i in a_tmp_dict:
        # print i
        if i["ID"] == undashed_uuid:
            project_name = i["Name"]
    # print project_name
    env_string = '''

#Copyright (c) Juniper Networks, Inc., 2017-2024.
#All rights reserved.
parameters:
    net_id1: %s

parameter_defaults:
    public_network: %s
    vfp_image: vPFE_17
    vfp_flavor: pfe-flv
    vcp_flavor: re-flv
    vcp_image: vRE_17
    project_name: %s
    gateway_ip: 0.0.0.0
    stack_name: VmxContrail 

resource_registry:
#  "OS::Nova::Vmx": vmx.yaml
  "OS::Nova::VmxContrail": vmx_contrail.yaml
#  "OS::Nova::VmxContrailSriov": vmx_contrail_sriov.yaml
  "OS::Nova::VmxRe": vmx-components/vms/re.yaml
  "OS::Nova::VmxFpc": vmx-components/vms/fpc.yaml
  "OS::Nova::VmxFpcSingle": vmx-components/vms/fpc_no_metadata.yaml
  "OS::Nova::VmxFpcSriov": vmx-components/vms/fpc_fixed_sriov.yaml
  "OS::Nova::VmxFpcVirtio": vmx-components/vms/fpc_fixed_virtio.yaml
  "OS::Networking::VmxFpcFixedNet": vmx-components/vms/fpc_fixed_net.yaml
  "OS::Networking::VmxIntNet": vmx-components/bridges/bridge_int.yaml
  "OS::Networking::VmxInternalNet": vmx-components/bridges/bridges_internal.yaml
  "OS::Networking::VmxInternalNetContrail": vmx-components/contrail/bridges_internal_contrail.yaml
  "OS::Networking::VmxIntNetContrail": vmx-components/contrail/bridge_int_contrail.yaml
  "OS::Networking::VmxNet": vmx-components/bridges/bridge_wan.yaml
  "OS::Networking::VmxNetContrail": vmx-components/contrail/bridge_wan_contrail.yaml
  "OS::Networking::VmxNetProvider": vmx-components/bridges/bridge_provider.yaml
  "OS::Networking::VmxProviderNetPort": vmx-components/ports/bridge_provider_port.yaml
  "OS::Networking::VmxProviderNetSriovPort": vmx-components/ports/bridge_provider_sriov_port.yaml
  "OS::Networking::VmxNet": vmx-components/bridges/bridge_wan.yaml
  "OS::Networking::VmxPort": vmx-components/ports/port.yaml
  "OS::Networking::VmxSriovPort": vmx-components/ports/sriov_port.yaml
  "OS::Networking::VmxContrailSriovPort": vmx-components/contrail/contrail_sriov_port.yaml
  "OS::Networking::VmFixedNet": vmx-components/vms/vm_fixed_net.yaml
  "OS::Networking::VmxPortWithIP": vmx-components/ports/port_with_ip.yaml
  "OS::Networking::VmxRePfePort": vmx-components/ports/re_pfe_port.yaml


''' % (net_2, net_1,  project_name)
    print env_string


def is_vmx_true():
    vmx_val = "false"
    if "vmx" in parsed_json["inp_params"]["params"]:
        vmx_val = parsed_json["inp_params"]["params"]["vmx"]
    print vmx_val

#screen -S test_screen -dm bash -c 'ls -ltrh; exec bash'
def create_screens_for_all_nodes_in_cluster_on_sm():
    change_network_dict()
    change_server_dict()
    a = subprocess.Popen('cat server-manager-file', shell=True, stdout=subprocess.PIPE)
    sm_ip = a.stdout.read()
    #print sm_ip
    for clus in server_dict:
        for i in server_dict[clus]:
	    if server_dict[clus][i]['server_manager'] != 'true':
		ip_dict = server_dict[clus][i]['ip_address']
		network_list = ip_dict.keys()
		#print network_list
		#print network_dict
		for j in network_list:
		    if network_dict[j]['role'] == 'management':
		        server_ip = ip_dict[j]
		#print server_ip			
		server_name = server_dict[clus][i]['name']
		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		client.connect(sm_ip, username = 'root', password = 'c0ntrail123')
		stdin, stdout, stderr = client.exec_command("apt-get install -y sshpass")
		time.sleep(5)
		stdin, stdout, stderr = client.exec_command("screen -S %s -dm bash -c 'sshpass -p c0ntrail123 ssh -o StrictHostKeyChecking=no root@%s; exec bash'" %(server_name, server_ip))
		client.close()	 
 
def get_compute_node_ip():
    fixedip_to_floatingip_mapping_dict = {}
    ret_list = []
    project_uuid = general_params_dict["project_uuid"]
    a = subprocess.Popen('neutron floatingip-list --tenant_id %s -f json' %
                         project_uuid, shell=True, stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp = str(a_tmp)
    fip_neutron_dict = eval(a_tmp)
    # print fip_neutron_dict
    for i in range(len(fip_neutron_dict)):
        fixedip_to_floatingip_mapping_dict[fip_neutron_dict[i]
                                           ["fixed_ip_address"]] = fip_neutron_dict[i]["floating_ip_address"]
    for clus in server_dict:
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                if "compute" in server_dict[clus][i]["roles"]:
                    for j in server_dict[clus][i]["ip_address"]:
                        if server_dict[clus][i]["ip_address"][j] in fixedip_to_floatingip_mapping_dict:
				ret_list.append(fixedip_to_floatingip_mapping_dict[server_dict[clus][i]["ip_address"][j]])
    ret_string = ','.join(ret_list)
    print ret_string

def get_compute_node_ip_mainline():
    fixedip_to_floatingip_mapping_dict = {}
    ret_list = []
    project_uuid = general_params_dict["project_uuid"]
    a = subprocess.Popen('neutron floatingip-list --tenant_id %s -f json' %
                         project_uuid, shell=True, stdout=subprocess.PIPE)
    a_tmp = a.stdout.read()
    a_tmp = str(a_tmp)
    fip_neutron_dict = eval(a_tmp)
    # print fip_neutron_dict
    for i in range(len(fip_neutron_dict)):
        fixedip_to_floatingip_mapping_dict[fip_neutron_dict[i]
                                           ["fixed_ip_address"]] = fip_neutron_dict[i]["floating_ip_address"]
    for clus in server_dict:
        for i in server_dict[clus]:
            if server_dict[clus][i]["server_manager"] != "true":
                if "contrail-compute" in server_dict[clus][i]["roles"]:
                    for j in server_dict[clus][i]["ip_address"]:
                        if server_dict[clus][i]["ip_address"][j] in fixedip_to_floatingip_mapping_dict:
                                ret_list.append(fixedip_to_floatingip_mapping_dict[server_dict[clus][i]["ip_address"][j]])
    ret_string = ','.join(ret_list)
    print ret_string
if __name__ == '__main__':
    globals()[sys.argv[2]]()
