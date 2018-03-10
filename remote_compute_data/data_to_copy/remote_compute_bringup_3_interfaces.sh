#Author: Soumil Kulkarni 
#Usage: ./remote_compute_bringup_3_interfaces.sh <New Project Name> <os for vm> <IP of base cluster config node> 
#Example: ./remote_compute_bringup_3_interfaces.sh RC_Project_1 ubuntu-14-04 10.87.66.138

source /etc/contrail/openstackrc
echo "The New Project Name is : " $1
echo "The Required OS for the Virtual Machines is :" $2
echo "Ip Address of the config node of the base cluster : " $3
os_name=$2
selected_config_node_ip=$3
a="$(openstack project create $1 -f json > uuid.json)"
openstack_project_uuid=$(python -c 'import json; fd=json.loads(open("uuid.json").read()); print fd["id"]')
dashed_project_uuid=$(python -c 'import uuid; fd=uuid.UUID("'${openstack_project_uuid}'"); print fd')
echo "Dashed UUID of the newly created Project is : " $dashed_project_uuid
rm uuid.json
keystone user-role-add --user admin --role admin --tenant $1

sed -i 's/project_uuid_val/'${dashed_project_uuid}'/' template_Remote_Compute
python change_testbed_params.py template_Remote_Compute $os_name parse_openstack_image_list_command
python change_testbed_params.py template_Remote_Compute vRE_18_1 get_vmx_images
python change_testbed_params.py template_Remote_Compute vPFE_18_1 get_vmx_images
python inp_to_yaml.py template_Remote_Compute check_and_create_required_flavor

sed -i 's/image_val/'${os_name}'/' template_Remote_Compute
fip_uuid="$(python change_testbed_params.py template_Remote_Compute $selected_config_node_ip get_fip_uuid)"
sed -i 's/fip_uuid/'${fip_uuid}'/' template_Remote_Compute

#sshpass -p "c0ntrail123" scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@10.84.24.64:/cs-shared/soumilk/remote_compute/Remote_compute_Automation/new_topology-try-2017-12-11/New_working_VMX/network.yaml .
#sshpass -p "c0ntrail123" scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no  root@10.84.24.64:/cs-shared/soumilk/remote_compute/Remote_compute_Automation/new_topology-try-2017-12-11/New_working_VMX/server.yaml .

python inp_to_yaml.py template_Remote_Compute create_network_yaml > network.yaml
python inp_to_yaml.py template_Remote_Compute create_server_yaml > server.yaml 

#sed -i 's/dashed_project_uuid/'${dashed_project_uuid}'/' network.yaml
#sed -i 's/dashed_project_uuid/'${dashed_project_uuid}'/' server.yaml

network_stack='remote_compute_network_stack'
final_network_stack_name=$network_stack$dashed_project_uuid
echo "Network Stack Name : " $final_network_stack_name
server_stack='remote_compute_server_stack'
final_server_stack_name=$server_stack$dashed_project_uuid
echo "Server Stack Name : " $final_server_stack_name

#python helper_functions.py 'dummy' get_ubuntu_14_04_image_for_vms
#python helper_functions.py 'dummy' get_fpc_image_for_vmx 
#python helper_functions.py 'dummy' get_re_image_for_vmx
#python helper_functions.py 'dummy' check_required_flavors


heat stack-create -f network.yaml $final_network_stack_name
sleep 3
while true
do
#python helper_functions.py $final_network_stack_name get_stack_status > tmp.txt
python change_testbed_params.py template_Remote_Compute $final_network_stack_name get_stack_status >  tmp.txt
chmod 777 tmp.txt
net_res="$(cat tmp.txt)"
#echo net_res
if [ "$net_res" == 'success' ] || [ "$net_res" == 'failed' ] || [ "$net_res" == 'inprogress' ];
then
        if [ "$net_res" == 'success' ]
        then
                echo "Network Stack Created Successfully"
                break
        fi
        if [ "$net_res" == 'failed' ]
        then
                echo "Network Stack Creation Failed "
                break
        fi
        if [ "$net_res" == 'inprogress' ]
        then
                echo "Network Stack creation still in progress. Waiting for 5 more seconds"
                heat stack-list | grep $final_network_stack_name
                sleep 5
        fi
else
        echo "Network Stack Creation: get_stack_status function in helper_functions.py file did not return any thing"
        break
fi
done
rm tmp.txt

if [ "$net_res" == 'success' ]
then
        heat stack-create -f server.yaml $final_server_stack_name
        sleep 10
        while true
        do
	#python helper_functions.py $final_server_stack_name get_stack_status > tmp.txt
	python change_testbed_params.py template_Remote_Compute $final_server_stack_name get_stack_status > tmp.txt
	ser_res="$(cat tmp.txt)"	
	if [ "$ser_res" == 'success' ] || [ "$ser_res" == 'failed' ] || [ "$ser_res" == 'inprogress' ];
        then
                if [ "$ser_res" == 'success' ]
                then
                        echo "Server Stack Created Successfully"
                        break
                fi
                if [ "$ser_res" == 'failed' ]
                then
                        echo "Server Stack Creation Failed"
                        heat stack-show $final_server_stack_name
                        exit 0
                fi
                if [ "$ser_res" == 'inprogress' ]
                then
                        echo "Server Stack Still in progress. Waiting for 20 more seconds"
                        heat stack-list | grep $final_server_stack_name
                        sleep 20
                fi
        else
                echo "Server Stack Creation: get_stack_status function in helper_functions.py file did not return any thing"
                break
        fi
        done
else
        echo "Network Stack Creation failed. So creation of the SERVER STACK is TERMINATED !!!!"
fi
rm tmp.txt

if [ "$ser_res" == 'success' ]
then

	sshpass -p "c0ntrail123" scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r root@10.84.24.64:/cs-shared/soumilk/remote_compute/Remote_compute_Automation/new_topology-try-2017-12-11/New_working_VMX/Tanvir_VMX/VMX_Bundle_Automation_3_interfaces .
	cp -r VMX_Bundle_Automation_3_interfaces/ VMX_Bundle_Automation_3_interfaces_1/
	cp -r VMX_Bundle_Automation_3_interfaces/ VMX_Bundle_Automation_3_interfaces_2/
	cd VMX_Bundle_Automation_3_interfaces/
	last_char_in_uuid=$(python -c 'a_tmp="'${dashed_project_uuid}'"; b_tmp = a_tmp.split("-"); print b_tmp[-1]')
	sed -i 's/_project_name_/'$1'/' vmx_contrail.env
	fixed_n_name='final_test_network_1_'$dashed_project_uuid
	sed -i 's/fixed_network_name/'${fixed_n_name}'/' vmx_contrail.env
	var_n_name='final_test_network_5_'$dashed_project_uuid
	sed -i 's/variable_network_name/'${var_n_name}'/' vmx_contrail.env
	var_n_name_1='final_test_network_6_'$dashed_project_uuid
	sed -i 's/var_net_n/'${var_n_name_1}'/' vmx_contrail.env
	heat stack-create -f vmx_contrail.yaml -e vmx_contrail.env RC_VMX_1_$last_char_in_uuid
	cd ..
	cd VMX_Bundle_Automation_3_interfaces_1/
	var_n_name='final_test_network_5_'$dashed_project_uuid				
	fixed_n_name='final_test_network_3_'$dashed_project_uuid	
	var_n_name_1='final_test_network_2_'$dashed_project_uuid
	sed -i 's/variable_network_name/'${var_n_name}'/' vmx_contrail.env
	sed -i 's/fixed_network_name/'${fixed_n_name}'/' vmx_contrail.env
	sed -i 's/var_net_n/'${var_n_name_1}'/' vmx_contrail.env
	sed -i 's/_project_name_/'$1'/' vmx_contrail.env
	heat stack-create -f vmx_contrail.yaml -e vmx_contrail.env RC_VMX_2_$last_char_in_uuid
	cd ..
	cd VMX_Bundle_Automation_3_interfaces_2/
	var_n_name='final_test_network_6_'$dashed_project_uuid
	fixed_n_name='final_test_network_4_'$dashed_project_uuid
	var_n_name_1='final_test_network_2_'$dashed_project_uuid
	sed -i 's/variable_network_name/'${var_n_name}'/' vmx_contrail.env
	sed -i 's/fixed_network_name/'${fixed_n_name}'/' vmx_contrail.env
	sed -i 's/var_net_n/'${var_n_name_1}'/' vmx_contrail.env
	sed -i 's/_project_name_/'$1'/' vmx_contrail.env
	heat stack-create -f vmx_contrail.yaml -e vmx_contrail.env RC_VMX_3_$last_char_in_uuid
fi
