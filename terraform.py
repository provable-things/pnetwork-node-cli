import json
import logging
import os
import time
import sys
from tqdm import tqdm
import hcl

import ansible as ans
import node
import utils as utl
from client_config import CLI_CONFIG


logger = logging.getLogger(__name__)

def replace_variables_tf(args_dict, node_name):
    '''
    Dynamically load variables template
    Loop and replace `/etc/pnode/terraform/variables.tf.json.orig`
    placeholders into `/etc/pnode/terraform/<node_name>/variables.tf.json`

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
    (terraform init works on dir so need to move into that folder in order to run
    terraform commands related to that instance [<node_name>.tfstate file])

    Args:
        param1: command to run
        param2: node name
    '''
    logger.info(f'Running: terraform {cmd}')
    tqdm.write(f'>>> running: terraform {cmd}')
    utl.run_cmd(f'cd {CLI_CONFIG["tf_config_dir"]}{node_name}; terraform {cmd} '
                f'>> {CLI_CONFIG["pcli_log_path"]} 2>&1')
    logger.info(f'Terraform {cmd}: complete')
    tqdm.write(f'>>> terraform {cmd}: complete')

def destroy_instance(node_name):
    '''
    Destroy instance and related file (by node name if running nodes > 1)

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
    Dynamically ask for values on stdin
    Write operator access_key_id and secret_key_id on instance path ~/.iam_credentials
    If `PICK` -> pickle state found, so check if key in PICK (var in state) and
    print in stdout as default to not loose last stdin values
    If no state found, ask user for value while printing a default

    Args:
        param1: key (from loop_inst_config_and_edit_dict())
        param2: value (from loop_inst_config_and_edit_dict())
        param3: value dict (from loop_inst_config_and_edit_dict())
        param4: [optional] PICK dict
        return: args dictionary got in input, edited (exit if `KeyboardInterrupt`)
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
        if i_key in ('access_key_id', 'secret_key_id'):
            new_val = str(input(f'>>> [node creation] insert {i_key} '
                                f'(default: {i_value}): ') or i_value)
        elif i_key in ('access_key_id', 'secret_key_id'):
            new_val = str(input(f'>>> [node operation] insert {i_key} '
                                f'(default: {i_value}): ') or i_value)
        else:
            new_val = str(input(f'>>> insert {i_key} (default: {i_value}): ') or i_value)
            iam_cred_dict[i_key[:-3]] = new_val
        json_iam_cred = json.dumps(iam_cred_dict)
        utl.write_file(json.loads(json_iam_cred), CLI_CONFIG['iam_cred_path'])
        if new_val != '':
            args_dict[i_key] = new_val
            return args_dict
    except KeyboardInterrupt:
        utl.write_file(args_dict, CLI_CONFIG['inst_state_path'], state=True)
        utl.run_cmd(f'rm -rf {CLI_CONFIG["tf_config_dir"]}/{node_name}')
        sys.exit(1)


def loop_inst_config_and_edit_dict(node_name):
    '''
    Load `inst_config` config file, loop it, call `input_str` to manage user inputs
    Save the edited file in path, based on `node_name`

    Args:
        param1: node name
        return: args dictionary, edited
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
    Ask for: [node]access_key_id, [node]secret_access_key, [operator]access_key_id,
             [operator]secret_access_key, inst_name and key_name

    Args:
        param1: node name
        return: args dictionary, edited
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
    Terraform instance provisioning, deploy the node via terraform, setup
    server w/ needed tools via ansible playbooks, start every service via pnode
    commands

    Args:
        param1: CLI args
        param2: [optional] update mode
    '''
    dev_mode = False
    if args.dev_mode is True:
        dev_mode = True
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
    p_bar = tqdm(total=100, bar_format='{desc} {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt}')
    p_bar.set_description('terraform init')
    tf_cmd('init', node_name)
    p_bar.update(5)
    try:
        p_bar.set_description('terraform plan')
        tf_cmd('plan', node_name)
        p_bar.update(15)
    except Exception as exc:
        logger.info(f'terraform plan error:\n{exc}')
        tqdm.write(f'>>> terraform plan error:\n{exc}')
        tqdm.write(f'>>> please run `pcli node clean -n {node_name}` to delete unused files')
        sys.exit(1)
    try:
        p_bar.set_description('terraform apply')
        if args.adv_mode is None:
            tf_cmd(f'apply -auto-approve', node_name)
        else:
            tf_cmd(f'apply', node_name)
        p_bar.update(15)
    except Exception as exc:
        logger.info(f'terraform apply error:\n{exc}')
        tqdm.write(f'>>> terraform apply error:\n{exc}')
        tqdm.write(f'>>> please run `pcli node clean -n {node_name}` to delete unused files')
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
        tqdm.write('>>> waiting for machine to be ready')
        p_bar.set_description('startup machine')
        time.sleep(40)
        p_bar.update(10)
        utl.scp_file('/home/ec2-user/.iam_credentials',
                     './.iam_credentials',
                     node_name, to_node=True)
        p_bar.set_description('install tools on machine')
        ans.sys_config(node_name)
        p_bar.update(5)
        p_bar.set_description('startup machine')
        new_rnd_pwd = utl.random_pwd_generator()
        pwd_file_content = (f'user: {CLI_CONFIG["inst_user"]} - pwd: '
                            f'{new_rnd_pwd} - IP: {pub_ip}\n')
        pwd_file_path = f'{CLI_CONFIG["tf_config_dir"]}{node_name}/.{node_name}-cred'
        utl.write_file(pwd_file_content, pwd_file_path)
        logger.info(f'Credentials dumped in {pwd_file_path}')
        tqdm.write(f'>>> credentials dumped in {pwd_file_path}')
        ans.edit_inst_user_pwd(node_name, new_rnd_pwd)
        p_bar.update(5)
        p_bar.set_description('startup machine')
        time.sleep(20)
        cred_file_echo_str = f"'{new_rnd_pwd}' > {CLI_CONFIG['inst_cred_path']}"
        utl.run_remote_cmd(f'"echo {cred_file_echo_str}"', node_name)
        p_bar.update(15)
        p_bar.set_description('reboot machine')
        utl.reboot_system(node_name)
        logger.info('Wait for machine to come back online after reboot')
        tqdm.write('>>> waiting for machine to come back online after reboot')
        time.sleep(120)
        p_bar.update(20)
        p_bar.set_description('setup node')
        if dev_mode is True:
            ans.deploy_pnode_package_playbook(node_name, CLI_CONFIG['pnetwork_pnode_url_dev'])
        else:
            ans.deploy_pnode_package_playbook(node_name, CLI_CONFIG['pnetwork_pnode_url'])
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
        p_bar.update(10)
        p_bar.close()
