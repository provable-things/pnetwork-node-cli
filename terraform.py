import json
import logging
import os
import time
import sys
import hcl

import ansible as ans
import node
import utils as utl
from client_config import CLI_CONFIG

logger = logging.getLogger(__name__)

def replace_variables_tf(args_dict, node_name):
    '''
    Dynamically load variables template
    Loop and replace variables.tf.json.orig placeholders
    File variables.tf.json saved

    Args:
        param1: config file
        param2: node name
    '''
    logger.info(f'Creating new {node_name}/variables.tf.json')
    print(f'>>> creating new {node_name}/variables.tf.json')
    with open(CLI_CONFIG['tf_variables_orig_path']) as tf_f:
        f_var_tf = json.dumps(hcl.load(tf_f))
    for key, value in args_dict.items():
        if isinstance(value, bool):
            f_var_tf = f_var_tf.replace('PH_' + key.upper(), str(value).lower())
        else:
            f_var_tf = f_var_tf.replace('PH_' + key.upper(), str(value))
    try:
        variables_tf_path = CLI_CONFIG['tf_config_dir'] + f'{node_name}/variables.tf.json'
        with open(variables_tf_path, 'w+') as f_new_var_tf:
            f_new_var_tf.write(f_var_tf)
            logger.info(f'File {node_name}/variables.tf.json correctly created')
            print(f'>>> file {node_name}/variables.tf.json correctly created')
    except Exception as exc:
        logger.error(f'Error writing {node_name}/variables.tf.json\n{exc}')
        print(utl.print_err_str(f'>>> error writing {node_name}/variables.tf.json'))

def tf_cmd(cmd, node_name):
    '''
    Move into terraform bin folder and run command
    (terraform init works on dir so need to move into that folder to run terraform commands
    related to that instance [*.tfstate file])

    Args:
        param1: command to run
        param2: node name
    '''
    logger.info(f'Running: terraform {cmd}')
    print(f'>>> running: terraform {cmd}')
    utl.run_cmd(f'cd {CLI_CONFIG["tf_config_dir"]}{node_name}; terraform {cmd} '
                f'>> {CLI_CONFIG["pcli_log_path"]} 2>&1')
    logger.info(f'Terraform {cmd}: complete')
    print(f'>>> terraform {cmd}: complete')

def destroy_instance(node_name):
    '''
    Destroy instance and related file
    Based on `node_name`

    Args:
        param1: node name
    '''
    if str(input(f'>>> DESTROY {node_name}? ARE YOU REALLY SURE? (y/n): ') or 'n') == 'y':
        logger.info(f'Destroy {node_name} confirmed')

        tf_cmd(f'destroy -auto-approve', node_name)
        utl.run_cmd(f'rm -rf {CLI_CONFIG["tf_config_dir"]}{node_name}')
        utl.run_cmd(f'rm -rf {CLI_CONFIG["pcli_ssh_key_path"]}{node_name}*')
        utl.run_cmd(f'rm -rf {CLI_CONFIG["ans_hosts_path"]}-{node_name}')
        utl.run_cmd(f'rm -rf {CLI_CONFIG["tf_config_dir"]}.{node_name}')
        logger.info(f'{node_name} destroyed')
        print(f'>>> {node_name} destroyed')

def input_str(i_key, i_value, args_dict, node_name, PICK=''):
    '''
    `if PICK` -> pickle state found, so check if key in PICK (var in state) and
    print in stdout as default
    if no state found, ask user for value while printing a default.

    Args:
        param1: key (from loop_inst_config_and_edit_dict()
        param2: value (from loop_inst_config_and_edit_dict()
        param3: value dict (from loop_inst_config_and_edit_dict()
        param4: [optional] PICK dict
        return: arg dictionary got in input, edited
    '''
    iam_cred_dict = {}
    try:
        if PICK:
            old_val = list({k:v for k, v in PICK.items() if k == i_key}.values())[0]
            new_val = str(input(f'>>> insert {i_key} (default: {i_value}) '
                                f'[old value found: {old_val}]: ') or old_val)
            if new_val != '':
                args_dict[i_key] = new_val
                return args_dict
        if i_key == 'access_key_id' or i_key == 'secret_key_id':
            new_val = str(input(f'>>> [node creation] insert {i_key} (default: {i_value}): ') or i_value)
        elif i_key == 'access_key_id' or i_key == 'secret_key_id':
            new_val = str(input(f'>>> [node operation] insert {i_key} (default: {i_value}): ') or i_value)
        else:
            new_val = str(input(f'>>> insert {i_key} (default: {i_value}): ') or i_value)
            iam_cred_dict[i_key[:-3]] = new_val
        json_iam_cred = json.dumps(iam_cred_dict)
        utl.write_file(json.loads(json_iam_cred), '/home/ec2-user/.iam_credentials')
        if new_val != '':
            args_dict[i_key] = new_val
            return args_dict
    except KeyboardInterrupt:
        utl.write_file(args_dict, CLI_CONFIG['inst_state_path'], state=True)
        utl.run_cmd(f'rm -rf {CLI_CONFIG["tf_config_dir"]}/{node_name}')
        sys.exit(1)


def loop_inst_config_and_edit_dict(node_name):
    '''
    Load inst_config, loop it, call `input_str` to manage user input
    Save the edited file in path, based on `node_name`

    Args:
        param1: instance name
        return: arg dictionary, edited
    '''
    state = False
    args_dict = json.load(open(CLI_CONFIG['inst_config_path']))
    if os.path.isfile(CLI_CONFIG['inst_state_path']):
        PICK = utl.read_file(CLI_CONFIG['inst_state_path'], state=True)
        state = True
    for key, value in args_dict.items():
        if key in ('access_key_id', 'secret_access_key') and os.getenv(key.upper()):
            logger.info('Found {key} in env')
            print('>>> found {key} in env')
            args_dict[key] = os.getenv(key.upper())
        elif key in ('inst_name', 'key_name', 'sg_name', 'sg_desc'):
            args_dict[key] = node_name
        elif key == 'priv_key_path':
            args_dict[key] = CLI_CONFIG['pcli_ssh_key_path'] + node_name
        elif key == 'pub_key_path':
            args_dict[key] = CLI_CONFIG['pcli_ssh_key_path'] + node_name + '.pub'
        elif key == 'region':
            args_dict[key] = utl.pick_up_a_region()
        else:
            if state is True and [k_s for k_s in PICK.keys() if key in k_s]:
                args_dict = input_str(key, value, args_dict, node_name, PICK=PICK)
            else:
                args_dict = input_str(key, value, args_dict, node_name)
    utl.run_cmd(f'rm -rf {CLI_CONFIG["inst_state_path"]}')
    return args_dict

def dump_default_variable_tf(node_name):
    '''
    Same as `loop_inst_config_and_edit_dict` but in non-advance mode
    Ask for: access_key_id, secret_access_key, inst_name and key_name

    Args:
        param1: node name
        return: arg dictionary, edited
    '''
    args_dict = json.load(open(CLI_CONFIG['inst_config_path']))
    az, ami = utl.pick_up_a_region()
    iam_cred_dict = {}
    for key in args_dict.keys():
        if key in ('access_key_id', 'secret_access_key') and os.getenv(key.upper()):
            logger.info('Found {key} in env')
            print('>>> found {key} in env')
            args_dict[key] = os.getenv(key.upper())
        elif key in ('inst_name', 'key_name', 'sg_name', 'sg_desc', 'vpc_name'):
            args_dict[key] = node_name
        elif key == 'priv_key_path':
            args_dict[key] = CLI_CONFIG['pcli_ssh_key_path'] + node_name
        elif key == 'pub_key_path':
            args_dict[key] = CLI_CONFIG['pcli_ssh_key_path'] + node_name + '.pub'
        elif key == 'region':
            args_dict[key] = az
        elif key == 'availability_zone':
            args_dict[key] = f'{az}a'
        elif key == 'inst_ami':
            args_dict[key] = ami
        elif key in ('access_key_id', 'secret_access_key') and not os.getenv(key.upper()):
            new_val = str(input(f'>>> [node creation] insert {key}: '))
            if new_val != '':
                args_dict[key] = new_val
        elif key in ('access_key_id_op', 'secret_access_key_op') and not os.getenv(key.upper()):
            new_val = str(input(f'>>> [node operator] insert {key[:-3]}: '))
            if new_val != '':
                args_dict[key] = new_val
            iam_cred_dict[key[:-3]] = new_val
            with open('./.iam_credentials', 'w') as f:
                f.write(json.dumps(iam_cred_dict))
    return args_dict, iam_cred_dict

def provisioning(args, update=False):
    '''
    Terraform instance provisioning:
    - check if it's an instance update or full provisioning
    - create the new node's folder (only if it's a provisioning)
    - copy the file `variables.tf.json`
    - copy the file `output.tf`
    - copy the file `main.tf`
    - init terraform and run `plan` to verify the new instance details
    - if confirmed, apply the plan, using the node's terraform's state file
    - only if update=False:
        - create the `hosts` file (named by `node_name`)
        - deploy tools and config via ansible
        - reboot the instance
        - run pnode commands in order to setup and run the node and its bridge

    Args:
        param1: CLI args
    '''
    print('>>> given your selection, we will be provisioning a pnetwork node of type NITRO')
    node_name = utl.random_name_generator()
    if update is False and utl.check_for_file_in_path(node_name,
                                                      CLI_CONFIG['tf_config_dir'],
                                                      isdir=True):
        logger.error(f'{node_name}: name already in use')
        print(f'>>> {node_name}: name already in use')
        sys.exit(1)
    if update is False:
        logger.info('Node provisioning called')
        print('>>> node provisioning called')
        print('>>> node name is valid')
        utl.run_cmd(f'mkdir -p {CLI_CONFIG["tf_config_dir"]}{node_name}')
        if not utl.check_for_file_in_path(f'{node_name}',
                                          CLI_CONFIG['pcli_ssh_key_path']):
            utl.create_ssh_keypair(node_name)
        else:
            logger.info(f'Found ssh keypair in {CLI_CONFIG["pcli_ssh_key_path"]}.ssh')
            print(f'>>> found ssh keypair in {CLI_CONFIG["pcli_ssh_key_path"]}.ssh')
    else:
        logger.info('Node update called')
        print('>>> node update called')
        print('>>> node name is valid')
    if args.adv_mode is None:
        args_dict, iam_cred_dict = dump_default_variable_tf(node_name)
        replace_variables_tf(args_dict, node_name)
    else:
        replace_variables_tf(loop_inst_config_and_edit_dict(node_name),
                             node_name)
    main_tf_path = CLI_CONFIG['tf_config_dir'] + f'{node_name}/main.tf'
    output_tf_path = CLI_CONFIG['tf_config_dir'] + f'{node_name}/output.tf'
    utl.copy_file_in_path(CLI_CONFIG['tf_main_orig_path'],
                          main_tf_path)
    utl.copy_file_in_path(CLI_CONFIG['tf_output_orig_path'],
                          output_tf_path)
    tf_cmd('init', node_name)
    try:
        tf_cmd('plan', node_name)
    except Exception as exc:
        logger.info(f'terraform plan error:\n{exc}')
        print(f'>>> terraform plan error:\n{exc}')
        print(f'>>> please run `pcli node clean -n {node_name}` to delete unused files')
        sys.exit(1)
    try:
        if args.adv_mode is None:
            tf_cmd(f'apply -auto-approve', node_name)
        else:
            tf_cmd(f'apply', node_name)
    except Exception as exc:
        logger.info(f'terraform apply error:\n{exc}')
        print(f'>>> terraform apply error:\n{exc}')
        print(f'>>> please run `pcli node clean -n {node_name}` to delete unused files')
        sys.exit(1)
    if update is False:
        pub_ip = utl.get_pub_ip(node_name)
        hosts_file_name = f'hosts-{node_name}'
        if not utl.check_for_file_in_path(hosts_file_name,
                                          CLI_CONFIG["ans_root"]):
            ans.write_ansible_hosts_file(pub_ip,
                                         CLI_CONFIG['inst_user'],
                                         CLI_CONFIG['pcli_ssh_key_path'] + node_name,
                                         node_name)
        logger.info('Wait for machine to be ready')
        print('>>> waiting for machine to be ready')
        time.sleep(40)
        utl.scp_file('/home/ec2-user/.iam_credentials', './.iam_credentials', node_name, to_node=True)
        ans.sys_config(node_name)
        new_rnd_pwd = utl.random_pwd_generator()
        pwd_file_content = (f'user: {CLI_CONFIG["inst_user"]} - '
                            f'{new_rnd_pwd}: {pub_ip}\n')
        pwd_file_path = f'{CLI_CONFIG["tf_config_dir"]}{node_name}/.{node_name}-cred'
        utl.write_file(pwd_file_content, pwd_file_path)
        logger.info(f'Credentials dumped in {pwd_file_path}')
        print(f'>>> credentials dumped in {pwd_file_path}')
        ans.edit_inst_user_pwd(node_name, new_rnd_pwd)
        time.sleep(20)
        utl.run_remote_cmd('echo "{new_rnd_pwd}" > {CLI_CONFIG["inst_cred_path"]}',
                           node_name)
        utl.reboot_system(node_name)
        logger.info('Wait for machine to come back online after reboot')
        print('>>> waiting for machine to come back online after reboot')
        time.sleep(120)
        ans.deploy_pnode_package_playbook(node_name)
        node.pnode_setup_and_start_cmds(node_name, new_rnd_pwd)
        print(utl.print_ok_str('##########################'))
        print(utl.print_ok_str('>>> configuration ended - details:'))
        print(utl.print_ok_str(f'>>> ec2-user password: {new_rnd_pwd}'))
        print(utl.print_ok_str(f'>>> {pub_ip} - {node_name}'))
        print(utl.print_ok_str('>>> remember to save the password!'))
        print(utl.print_ok_str('>>> node dashboard details:'))
        print(utl.print_ok_str(f'>>> http://{pub_ip}:8080'))
        print(utl.print_ok_str('>>> user: operator'))
        print(utl.print_ok_str(f'>>> password: {new_rnd_pwd}'))
