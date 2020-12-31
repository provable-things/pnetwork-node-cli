import logging
import sys

import utils as utl
from client_config import CLI_CONFIG

logger = logging.getLogger(__name__)

def write_ansible_hosts_file(pub_ip, inst_user, ssh_priv_key_path, node_name):
    '''
    Write hosts file for ansible from template, based on `node_name`

    Args:
        param1: public IP
        param2: instance user
        param3: path of the ssh private key
        param4: node name
    '''
    logger.info('Writing ansible\'s hosts file...')
    print('>>> writing ansible\'s hosts file...')
    try:
        hosts_path = f'{CLI_CONFIG["ans_hosts_path"]}-{node_name}'
        cont = (f'[nodes]\n{pub_ip} ansible_ssh_user={inst_user}'
                f' ansible_ssh_private_key_file={ssh_priv_key_path}')
        utl.write_file(cont, hosts_path)
        logger.info('Ansible hosts file created')
        print('>>> ansible hosts file created')
    except Exception as exc:
        logger.error(f'Error writing hosts file for ansible\n{exc}')
        print(utl.print_err_str('>>> error writing hosts file for ansible'))

def run_playbook(ans_playbooks_path,
                 ans_playbook_name,
                 ans_hosts_path,
                 extra_vars=None):
    '''
    Run selected ansible playbook on the instance

    Args:
        param1: playbook file path
        param2: playbook file name
        param3: hosts file path
        param4: [optional] pass extra var to ansible
    '''
    if extra_vars is None:
        logger.info('Running playbooks')
        print('>>> running ansible playbooks')
        try:
            utl.run_cmd('ANSIBLE_HOST_KEY_CHECKING=False '
                        f'ansible-playbook '
                        f'{ans_playbooks_path}{ans_playbook_name} -i '
                        f'{ans_hosts_path} >> {CLI_CONFIG["pcli_log_path"]} 2>&1')
        except Exception as exc:
            logger.error(f'error while running ansible {ans_playbook_name} playbook:\n{exc}')
            print(f'>>> error while running ansible {ans_playbook_name} playbook')
            sys.exit(1)
    else:
        logger.info('Running playbooks')
        print('>>> running ansible playbooks')
        try:
            utl.run_cmd('ANSIBLE_HOST_KEY_CHECKING=False '
                        f'ansible-playbook '
                        f'{ans_playbooks_path}{ans_playbook_name} -i '
                        f'{ans_hosts_path} --extra-vars "new_pwd={extra_vars}" '
                        f'>> {CLI_CONFIG["pcli_log_path"]} 2>&1')
        except Exception as exc:
            logger.error(f'error while running ansible {ans_playbook_name} playbook')
            print(f'>>> error while running ansible {ans_playbook_name} playbook')
            sys.exit(1)

def sys_config(node_name):
    '''
    Config system via ansible playbook (`sys_config.yml`) - which will install
    all the needed tools on the instance
    '''
    logger.info('Deploying sys_config ansible playbook')
    print('>>> deploying sys_config ansible playbook')
    hosts_path = f'{CLI_CONFIG["ans_hosts_path"]}-{node_name}'
    run_playbook(CLI_CONFIG['ans_playbooks_path'],
                 'sys_config.yml',
                 hosts_path)

def deploy_pnode_package_playbook(node_name):
    '''
    Run  pnode_package playbook - which will install
    all the pnode tools on the instance via rpm

    Args:
        param1: node name
    '''
    logger.info('Deploying pnode_package ansible playbook')
    print('>>> deploying pnode_package ansible playbook')
    hosts_path = f'{CLI_CONFIG["ans_hosts_path"]}-{node_name}'
    run_playbook(CLI_CONFIG['ans_playbooks_path'],
                 'pnode_package.yml',
                 hosts_path)

def edit_inst_user_pwd(node_name, pwd):
    '''
    Run playbook to edit the instance user pwd with a random generated one

    Args:
        param1: node name
        param2: user password
    '''
    hosts_path = f'{CLI_CONFIG["ans_hosts_path"]}-{node_name}'
    run_playbook(CLI_CONFIG['ans_playbooks_path'],
                 'edit_user_pwd.yml',
                 hosts_path,
                 extra_vars=pwd)
