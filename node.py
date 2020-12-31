import logging
import time
import sys

import terraform as trf
import utils as utl
from client_config import CLI_CONFIG

logger = logging.getLogger(__name__)

def ssh_into_node(node_name):
    '''
    Open a ssh tunnel on the instance, by node-name

    Args:
        param1: node name
    '''
    try:
        logger.info('Opening ssh tunnel')
        print('>>> opening ssh tunnel')
        pub_ip = utl.get_pub_ip(node_name)
        priv_key_path = CLI_CONFIG['pcli_ssh_key_path'] + node_name
        utl.run_cmd(f'ssh -o StrictHostKeyChecking=no -i {priv_key_path} '
                    f'{CLI_CONFIG["inst_user"]}@{pub_ip}', output=False,
                    nowait=False, noerr=True)
    except Exception as exc:
        logger.error(f'Error retrieving node\'s pub IP\n{exc}')
        print(utl.print_err_str('>>> error retrieving node\'s pub IP'))
        logger.error(f'Error opening ssh tunnel\n{exc}')
        print(utl.print_err_str('>>> error opening ssh tunnel'))

def exec_cmd_on_node(args, node_name):
    '''
    Remote execute command/script on the instance, by node-name

    Args:
        param1: CLI args
    '''
    if args.exec_script:
        res = utl.run_remote_script(args.exec_script, node_name)
        logger.info(f'{res} returned')
    else:
        res = utl.run_remote_cmd(args.cmd_to_exec, node_name)
        logger.info(f'{res} returned')

def update_pnode_pkg(node_name, pkg=None):
    '''
    Update single subpackage or whole pnode package

    Args:
        param1: node name
        param2: pkg name if single
    '''
    if pkg is None or (len(pkg) == 1 and 'all' in pkg):
        logger.info('Update pnode')
        print('>>> update pnode')
        utl.run_remote_cmd('sudo yum clean all', node_name, output=False)
        utl.run_remote_cmd('sudo yum info pnode-nitro*', node_name, output=False)
        utl.run_remote_cmd('sudo yum update pnode-nitro* -y', node_name, output=False)
    elif pkg is not None and (len(pkg) > 1 and 'all' not in pkg):
        for pk in pkg:
            logger.info(f'Update {pk}')
            print(f'>>> update {pk}')
            utl.run_remote_cmd(f'sudo yum update {pk} -y', node_name, output=False)
    elif pkg is not None and (len(pkg) == 1 and 'all' not in pkg):
        logger.info(f'Update {pkg[0]}')
        print(f'>>> update {pkg[0]}')
        utl.run_remote_cmd(f'sudo yum update {pkg[0]} -y', node_name, output=False)
    else:
        logger.error('Unexpected package to update')
        print(utl.print_err_str('Unexpected package to update'))
        sys.exit(1)

def node_clean(node_name):
    '''
    Delete unused config file (due to error on tf, ansible, etc)

    Args:
        param1: node name
    '''
    utl.run_cmd(f'rm -rf {CLI_CONFIG["tf_config_dir"]}{node_name}')
    logger.error(f'{node_name}: terraform folder deleted')
    print(f'>>> {node_name}: terraform folder deleted')
    utl.run_cmd(f'rm -rf {CLI_CONFIG["ans_hosts_path"]}-{node_name}')
    logger.error(f'{node_name}: ansible host file deleted')
    print(f'>>> {node_name}: ansible host file deleted')
    utl.run_cmd(f'rm -rf {CLI_CONFIG["pcli_ssh_key_path"]}{node_name}*')
    logger.error(f'{node_name}: ssh keypair deleted')
    print(f'>>> {node_name}: ssh keypair deleted')

def pnode_setup_and_start_cmds(node_name, new_rnd_pwd):
    '''
    Run pnode tools suite commands on node

    Args:
        param1: node name
        param2: password
    '''
    try:
        utl.run_remote_cmd(f'pnode_logs_viewer start >> {CLI_CONFIG["pcli_log_path"]} 2>&1',
                           node_name,
                           output=True)
        print('>>> starting all pnode_nitro components')
    except Exception as exc:
        logger.error(f'Error running pnode_logs_viewer_start:\n{exc}')
        print('>>> error running pnode_logs_viewer_start')
    try:
        utl.run_remote_cmd(f'pnode_nitro_enclave deploy >> {CLI_CONFIG["pcli_log_path"]} 2>&1',
                           node_name,
                           output=True)
    except Exception as exc:
        logger.error(f'Error running pnode_nitro_enclave deploy: \n{exc}')
        print('>>> error running pnode_nitro_enclave deploy')
    try:
        utl.run_remote_cmd(f'pnode_nitro_enclave start >> {CLI_CONFIG["pcli_log_path"]} 2>&1',
                           node_name,
                           output=False,
                           nowait=True)
    except Exception as exc:
        logger.error(f'Error running pnode_nitro_enclave start: \n{exc}')
        print('>>> error running pnode_nitro_enclave start')
    try:
        time.sleep(60)
        utl.run_remote_cmd(f'ptokens_bridge deploy >> {CLI_CONFIG["pcli_log_path"]} 2>&1',
                           node_name,
                           output=True)
    except Exception as exc:
        logger.error(f'Error running ptokens_bridge deploy: \n{exc}')
        print('>>> error running ptokens_bridge deploy')
    try:
        start_dashboard_cmd = f'pnode_dashboard start {new_rnd_pwd} >> {CLI_CONFIG["pcli_log_path"]} 2>&1'
        utl.run_remote_cmd(start_dashboard_cmd, node_name, output=True)
    except Exception as exc:
        logger.error(f'Error running pnode_dashboard start {new_rnd_pwd}:\n{exc}')
        print(f'>>> error running pnode_dashboard start {new_rnd_pwd}')


def node_mng(args):
    '''
    Manage all the `node` commands and:
    - check arg `node_name`
    - check if `provider` arg not null when provisioning an instance
    - check if `provider` is `aws`

    Args:
        param1: CLI args
    '''
    if args.action[0] in ('destroy', 'exec',
                          'ssh', 'update') and utl.get_inst_list(nodes_nr=True) > 1:
        if args.node_name is None:
            logger.error('More than one running node found - the following argument '
                         'is required: node name')
            print('>>> more than one running node found - the following argument is '
                  ' required: node name')
            sys.exit(1)
        else:
            node_name = args.node_name
    elif args.action[0] in ('destroy', 'exec',
                            'ssh', 'update') and utl.get_inst_list(nodes_nr=True) == 1:
        node_name = utl.get_inst_list(nodes_nr=False, single_node=True)
    if args.action[0] == 'provisioning' and args.node_name is not None:
        logger.error('The following arguments is not required: node name')
        print('>>> error - the following arguments is not required: node name')
        sys.exit(1)
    if args.action[0] == 'clean' and args.node_name is None:
        logger.error('The following arguments is required: node name')
        print('>>> error - the following arguments is required: node name')
        sys.exit(1)
    if args.action[0] == 'clean':
        logger.info('Run command node clean')
        node_clean(args.node_name)
    elif args.action[0] == 'edit':
        logger.info('Run command node edit')
        trf.provisioning(args, update=True)
    elif args.action[0] == 'exec':
        logger.info('Run command exec on node')
        exec_cmd_on_node(args, node_name)
    elif args.action[0] == 'list':
        logger.info('Run command node list')
        utl.get_inst_list()
    elif args.action[0] == 'destroy':
        logger.info('Run command node destroy')
        trf.destroy_instance(node_name)
    elif args.action[0] == 'provisioning':
        logger.info('Run command node provisioning')
        trf.provisioning(args)
    elif args.action[0] == 'ssh':
        logger.info('Run command node ssh')
        ssh_into_node(node_name)
    elif args.action[0] == 'update':
        logger.info('Update pnode package')
        update_pnode_pkg(node_name, pkg=args.pkg_name)
