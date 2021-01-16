import logging
import sys

import utils as utl


logger = logging.getLogger(__name__)

def bridge_mng(args):
    '''
    Manage the bridge commands:
    - start, stop, restart and deploy (single/all) container/s by node-name
    (and bridge name if not `all`)

    Args:
        param1: cli args
    '''
    if args.action[0] in ('start', 'restart', 'stop', 'deploy') and args.bridge_comp[0] == 'all':
        cmd = f'ptokens_bridge {args.action[0]}'
        utl.run_remote_cmd(cmd, args.node_name)
    elif args.action[0] in ('start_single',
                            'restart_single',
                            'stop_single') and args.bridge_comp[0] != 'all':
        cmd = f'ptokens_bridge {args.action[0]} {args.bridge_comp[0]}'
        utl.run_remote_cmd(cmd, args.node_name)
    elif args.action[0] in ('start_single',
                            'restart_single',
                            'stop_single') and args.bridge_comp[0] is None:
        logger.error('The following arguments are required: component name')
        print('>>> the following arguments are required: component name')
        sys.exit(1)
