import json
import logging
import os
import pickle
import random
import string
import subprocess
import random_name
import yaml

from client_config import CLI_CONFIG


__version__ = '0.1-1'

logger = logging.getLogger(__name__)

def print_err_str(err_str):
    '''
    Return red-colored string for errors

    Args:
        param1: string
        return: red-colored string
    '''
    return f'\x1b[1;31m{err_str}\x1b[0m'

def print_ok_str(ok_str):
    '''
    Return green-colored string for ok

    Args:
        param1: string
        return: green-colored string
    '''
    return f'\x1b[1;32m{ok_str}\x1b[0m'

def check_for_pcli_updates(args):
    '''
    Print installed version and gh repo link

    Args:
        param1: cli args
    '''
    print(f'>>> installed version: {__version__}')
    print('>>> please check out '
          'https://github.com/provable-things/pnetwork-node-cli/tree/master '
          'for updates')

def scp_file(file_rem_path, file_loc_path, node_name, to_node=False):
    '''
    scp file to/from instance by files path and node name (`to_node=True` so send)

    Args:
        param1: remote file path
        param2: local file path
        param3: node name
        param4: [optional] send file to node
    '''
    try:
        pub_ip = get_pub_ip(node_name)
        priv_key_path = CLI_CONFIG['pcli_ssh_key_path'] + node_name
        if to_node is True:
            run_cmd((f'scp -i {priv_key_path} -o StrictHostKeyChecking=no '
                     '-o UserKnownHostsFile=/dev/null -q '
                     f'{file_loc_path} {CLI_CONFIG["inst_user"]}@{pub_ip}:{file_rem_path}'))
        else:
            run_cmd((f'scp -i {priv_key_path} -q '
                     f'{CLI_CONFIG["inst_user"]}@{pub_ip}:{file_rem_path} '
                     f'{file_loc_path}'))
    except Exception as exc:
        logger.error(f'scp error on {node_name}\n{exc}')
        print(print_err_str(f'>>> scp error on {node_name}'))

def run_remote_cmd(cmd, node_name, output=False, nowait=False, comm=False):
    '''
    Run raw command on remote instance

    Args:
        param1: raw command
        param2: node name
        return: stdout result string
    '''
    if output is True:
        try:
            pub_ip = get_pub_ip(node_name)
            priv_key_path = CLI_CONFIG['pcli_ssh_key_path'] + node_name
            res = run_cmd((f'ssh -i {priv_key_path} '
                           f'{CLI_CONFIG["inst_user"]}@{pub_ip} '
                           f'{cmd}'), output=True)
            return res
        except Exception as exc:
            logger.error(f'Error running command {cmd} on {node_name}\n{exc}')
            print(print_err_str(f'>>> error running command {cmd} on {node_name}'))
    elif nowait is True:
        try:
            pub_ip = get_pub_ip(node_name)
            priv_key_path = CLI_CONFIG['pcli_ssh_key_path'] + node_name
            run_cmd((f'ssh -i {priv_key_path} '
                     f'{CLI_CONFIG["inst_user"]}@{pub_ip} '
                     f'{cmd}'), nowait=True)
        except Exception as exc:
            logger.error(f'Error running command {cmd} on {node_name}\n{exc}')
            print(print_err_str(f'>>> error running command {cmd} on {node_name}'))
    elif comm is True:
        try:
            pub_ip = get_pub_ip(node_name)
            priv_key_path = CLI_CONFIG['pcli_ssh_key_path'] + node_name
            run_cmd((f'ssh -i {priv_key_path} '
                     f'{CLI_CONFIG["inst_user"]}@{pub_ip} '
                     f'{cmd}'), comm=True)
        except Exception as exc:
            logger.error(f'Error running command {cmd} on {node_name}\n{exc}')
            print(print_err_str(f'>>> error running command {cmd} on {node_name}'))
    else:
        try:
            pub_ip = get_pub_ip(node_name)
            priv_key_path = CLI_CONFIG['pcli_ssh_key_path'] + node_name
            run_cmd(f'ssh -i {priv_key_path} '
                    f'{CLI_CONFIG["inst_user"]}@{pub_ip} {cmd}')
        except Exception as exc:
            logger.error(f'Error running command {cmd} on {node_name}\n{exc}')
            print(print_err_str(f'>>> error running command {cmd} on {node_name}'))

def run_remote_script(script_path, node_name):
    '''
    Run script on remote instance

    Args:
        param1: script local path
        param2: node name
        return: stdout result string
    '''
    try:
        pub_ip = get_pub_ip(node_name)
        priv_key_path = CLI_CONFIG['pcli_ssh_key_path'] + node_name
        res = run_cmd((f'ssh -i {priv_key_path} '
                       f'{CLI_CONFIG["inst_user"]}@{pub_ip} '
                       f'bash -s < {script_path}'), output=True)
        return res
    except Exception as exc:
        logger.error(f'Error running script {script_path} on {node_name}\n{exc}')
        print(print_err_str(f'>>> error running script {script_path} on {node_name}'))

def run_cmd(cmd, output=False, nowait=False, noerr=False, comm=False):
    '''
    Run command on host, if `output=True` return stdout result

    Args:
        param1: command
        return: stdout result (if `output=True`)
    '''
    if output is True:
        try:
            res = subprocess.check_output(cmd, shell=True)
            return res.decode('utf-8').rstrip()
        except Exception as exc:
            logger.error(f'Error running command {cmd}\n{exc}')
            print(print_err_str(f'>>> error running command {cmd}'))
    elif nowait is True:
        try:
            subprocess.Popen(cmd, close_fds=True, shell=True)
            logger.info(f'{cmd} started in backgroud')
        except Exception as exc:
            logger.error(f'Error running command {cmd}\n{exc}')
            print(print_err_str(f'>>> error running command {cmd}'))
    elif noerr is True:
        try:
            subprocess.run(f'{cmd}', shell=True)
            logger.info(f'{cmd} started')
        except Exception as exc:
            logger.error(f'Error running command {cmd}\n{exc}')
    elif comm is True:
        try:
            res = subprocess.run(cmd, shell=True)
        except Exception as exc:
            logger.error(f'Error running command {cmd}\n{exc}')
    else:
        try:
            subprocess.run(cmd, shell=True, check=True)
            return None
        except Exception as exc:
            logger.error(f'Error running command {cmd}\n{exc}')
            print(print_err_str(f'>>> error running command {cmd}'))

def reboot_system(node_name):
    '''
    Reboot instance by node name

    Args:
       param1: node name
    '''
    logger.info('Rebooting system')
    print('>>> rebooting system')
    run_remote_cmd('sudo shutdown -r +1', node_name)

def get_inst_list(nodes_nr=False, single_node=False):
    '''
    Print list of active nodes (name: IP)
    Find folders in path which are not the defaults
    `nodes_nr=True` return nr of nodes
    `single_node=True` return single node name

    Args:
        param1: [optional] return nr of nodes
        param2: [optional] return single node name
    '''
    tf_form_dir = os.path.abspath(
                      os.path.expanduser(
                          os.path.expandvars(CLI_CONFIG['tf_config_dir'])))
    for root, dirs, files in os.walk(tf_form_dir):
        # Get dirs with depth=1
        if root[len(tf_form_dir):].count(os.sep) < 1:
            n_list = dirs
    if nodes_nr is False and single_node is False:
        if len(n_list) == 0:
            logger.info('No active nodes')
            print('>>> no active nodes')
        else:
            for node in n_list:
                node_ip = get_pub_ip(node)
                logger.info(f'{node}: {node_ip} listed')
                print(f'>>> {node}: {node_ip}')
    elif single_node is True:
        return n_list[0]
    else:
        return len(n_list)

def get_pub_ip(node_name):
    '''
    Return nodes's public IP via `terraform output` using the proper state file
    If error, returns `unknown ip`

    Args:
        param1: node name
        return: public ip
    '''
    logger.info('Asking for instances\'s public ip')
    try:
        tf_state_path = CLI_CONFIG['tf_state_path'] + node_name + '/terraform.tfstate'
        ip_name = run_cmd(f'terraform output -json -state={tf_state_path}',
                          output=True)
        return json.loads(ip_name)['public_ip']['value'][0]
    except Exception as exc:
        logger.error(f'Error parsing public IP from terraform-output\n{exc}')
        return 'unknown ip'

def read_file(file_path, yaml_f=False, state=False):
    '''
    Read file from path and return its content
    Works also for yaml and pickle

    Args:
        param1: file path
        param2: [optional] yaml format
        param3: [optional] pickle format
        return: file content
    '''
    try:
        if yaml_f is True:
            with open(file_path) as f_yaml:
                yaml_file = yaml.safe_load(f_yaml)
            return yaml_file
        if state is True:
            with open(file_path, 'rb') as f_state:
                state_file = pickle.load(f_state)
            return state_file
    except Exception as exc:
        logger.error(f'Error while loading {file_path}\n{exc}')
        print(print_err_str('>>> error while loading {file_path}'))

def write_file(file_content, dest_path, file_list=False, state=False):
    '''
    Write data on a given path as file
    Works also for lists and pickle files

    Args:
        param1: file content
        param2: destination path
        param3: [optional] list format
        param4: [optional] pickle format
    '''
    try:
        if file_list is True:
            with open(dest_path, 'a') as f_list:
                for row in file_content:
                    f_list.write(row)
        elif state is True:
            with open(dest_path, 'ab') as f_state:
                pickle.dump(file_content, f_state)
        else:
            with open(dest_path, 'a') as f_gen:
                f_gen.write(file_content)
            logger.info(f'{dest_path} saved')
            print(f'>>> {dest_path} saved')
    except Exception as exc:
        logger.error(f'Error while writing {dest_path}\n{exc}')
        print(print_err_str('>>> error while writing {dest_path}'))

def check_for_file_in_path(file_name, path, isdir=False, no_stdout=False):
    '''
    Check for file in a given path

    Args:
        param1: file name
        param2: file path
        param3: [optional] search for dir
        param4: [optional] disable stdout
        return: `True` if found, `False` if not
    '''
    if isdir is True:
        if os.path.isdir(f'{path}{file_name}'):
            logger.info(f'{path}{file_name} found')
            print(f'>>> {path}{file_name} found')
            return True
    if no_stdout is True:
        if os.path.isfile(f'{path}{file_name}'):
            logger.info(f'{path}{file_name} found')
            return True
        logger.info(f'{path}{file_name} not found')
        return False
    if os.path.isfile(f'{path}{file_name}'):
        logger.info(f'{path}{file_name} found')
        print(f'>>> {path}{file_name} found')
        return True
    logger.info(f'{path}{file_name} not found')
    print(f'>>> {path}{file_name} not found')
    return False

def copy_file_in_path(origin, dest):
    '''
    Copy file (full path) in a given path

    Args:
        param1: origin file
        param2: destination file
    '''
    run_cmd(f'cp -r {origin} {dest}')

def create_ssh_keypair(key_name):
    '''
    Create a 4096 RSA ssh keypair and store it in ~/.pcli/.ssh
    key_name == node_name

    Args:
        param1: ssh key-pair name
    '''
    dest_path = f'{CLI_CONFIG["pcli_ssh_key_path"]}{key_name}'
    logger.info('Creating ssh keypair')
    print('>>> creating ssh keypair')
    run_cmd(f'ssh-keygen -b 4096 -t rsa -f {dest_path} -q -N ""')
    run_cmd(f'chmod 600 {CLI_CONFIG["pcli_ssh_key_path"]}{key_name}')

def pick_up_a_region():
    '''
    Print AZ list to user during provisioning
    Map key with AZ short-name, then map AZ with AMI
    Return selected AZ and its relative AMI

    Args:
        return: choosen region and ami
    '''
    az = input('>>> select your region of choice (by number)\n'
               '>>> 1 - N.Virginia\n'
               '>>> 2 - Oregon\n'
               '>>> 3 - N.California\n'
               '>>> 4 - Ireland\n'
               '>>> 5 - Frankfurt\n'
               '>>> 6 - Singapore\n'
               '>>> 7 - Tokyo\n'
               '>>> 8 - Sydney\n'
               '>>> 9 - Seoul\n'
               '>>> 10 - San Paulo\n'
               '>>> 11 - London\n'
               '>>> 12 - Mumbai\n'
               '>>> choice: ') or 1
    AZ_MAP = {1: 'us-east-1',
              2: 'us-west-2',
              3: 'us-west-1',
              4: 'eu-west-1',
              5: 'eu-central-1',
              6: 'ap-southeast-1',
              7: 'ap-northeast-1',
              8: 'ap-southeast-2',
              9: 'ap-northeast-2',
              10: 'sa-east-1',
              11: 'eu-west-2',
              12: 'ap-south-1'}
    sel_az = AZ_MAP[int(az)]
    print(f'>>> {sel_az} selected')
    AMI_MAP = {'us-east-1': 'ami-0be2609ba883822ec',
               'us-west-2': 'ami-0a36eb8fadc976275',
               'us-west-1': 'ami-03130878b60947df3',
               'eu-west-1': 'ami-01720b5f421cf0179',
               'eu-central-1': 'ami-03c3a7e4263fd998c',
               'ap-southeast-1': 'ami-00b8d9cb8a7161e41',
               'ap-northeast-1': 'ami-01748a72bed07727c',
               'ap-southeast-2': 'ami-06ce513624b435a22',
               'ap-northeast-2': 'ami-0094965d55b3bb1ff',
               'sa-east-1': 'ami-022082b7f1da62478',
               'eu-west-2': 'ami-0e80a462ede03e653',
               'ap-south-1': 'ami-04b1ddd35fd71475a'}
    sel_ami = AMI_MAP[sel_az]
    print(f'>>> {sel_ami} selected')
    return sel_az, sel_ami

def random_pwd_generator():
    '''
    Create a random password based on alphanumerics char - 36 chars long - and
    print it in stdout

    Args:
        return: generated pwd
    '''
    pwd_chars = string.ascii_letters + string.digits
    pwd = ''.join(random.choice(pwd_chars) for i in range(36))
    logging.info('Random password generated')
    print('>>> random password generated')
    return pwd

def random_name_generator():
    '''
    Create random name (docker style) for instance

    Args:
        return: generated name
    '''
    node_name = random_name.generate_name().split('-', 1)[1]
    logging.info('Random instance name generated')
    logging.info(f'Instance name: {node_name}')
    print('>>> random instance name generated')
    print(f'>>> ec2-user instance name: {node_name}')
    print('>>> remember to save the instance name!')
    return node_name
