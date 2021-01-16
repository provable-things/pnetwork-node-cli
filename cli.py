import argparse
import logging
import logging.config

import bridge as brg
import node
import utils as utl
from client_config import CLI_CONFIG


def main():
    '''
    Start pCLI, initialize logger and argparse
    '''

    logger = logging.getLogger(__name__)

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': ('%(asctime)s - %(levelname)s - '
                           '%(module)s: %(funcName)s - '
                           '%(name)s: %(message)s')
            },
        },
        'handlers': {
            'default': {
                'level':'DEBUG',
                'class':'logging.FileHandler',
                'filename': CLI_CONFIG['pcli_log_path'],
                'formatter': 'simple'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': 0
            }
        }
        })

    parser = argparse.ArgumentParser('pcli')
    parser.add_argument('-v', action='version', version=utl.__version__)
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    p_bridge_commands = subparsers.add_parser('bridge', help='interact with bridge\'s components')
    p_bridge_commands.set_defaults(func=brg.bridge_mng)
    p_bridge_commands.add_argument(nargs=1,
                                   choices=['start', 'stop', 'restart',
                                            'deploy', 'start_single', 'stop_single',
                                            'restart_single'],
                                   dest='action',
                                   help='specify action')
    p_bridge_commands.add_argument(nargs=1,
                                   choices=['api',
                                            'syncer_native',
                                            'syncer_host',
                                            'all'],
                                   dest='bridge_comp',
                                   help='specify component')
    p_bridge_commands.add_argument('-n',
                                   required=True,
                                   metavar='',
                                   dest='node_name',
                                   help='select node')

    p_node = subparsers.add_parser('node',
                                   help='interact with nodes')
    p_node.set_defaults(func=node.node_mng)
    p_node.add_argument('-n',
                        metavar='',
                        dest='node_name',
                        help='node name')
    p_node.add_argument('-p',
                        nargs='+',
                        metavar='',
                        dest='pkg_name',
                        help='package name (`all` for whole package)')
    p_node.add_argument('-a',
                        metavar='',
                        dest='adv_mode',
                        help='advanced mode for provisioning')
    p_node.add_argument('-s',
                        metavar='',
                        dest='exec_script',
                        help='run script on node')
    p_node.add_argument('--dev',
                        action='store_true',
                        dest='dev_mode',
                        help='dev mode')
    p_node.add_argument(nargs=1,
                        choices=['clean',
                                 'destroy',
                                 'exec',
                                 'list',
                                 'provisioning',
                                 'ssh',
                                 'update'],
                        dest='action',
                        help='specify action')
    p_node.add_argument(nargs='?',
                        metavar='',
                        dest='cmd_to_exec',
                        help='run cmd on node')

    p_update = subparsers.add_parser('update', help='update pCLI')
    p_update.set_defaults(func=utl.check_for_pcli_updates)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
