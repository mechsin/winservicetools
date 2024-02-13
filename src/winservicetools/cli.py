
import argparse
import os

from winservicetools import utils

def cli_main():
	
    script_pargs = ('--script',)
    script_kwargs = {
                     'dest': 'script_path',
                     'required': False,
                     'type': os.path.abspath,
                    }
    package_pargs = ('--import',)
    package_kwargs = {
                      'dest': 'import_name',
                      'required': False,
                     }
    
    desc = 'Install Python services via sc.exe'
    parser = argparse.ArgumentParser(description=desc)
    subparsers = parser.add_subparsers()
    
    # Installer subparser
    parser_install = subparsers.add_parser('install', help='Install services')
    parser_install.set_defaults(func=utils.install)
    group = parser_install.add_mutually_exclusive_group(required=True)
    ts_kwargs = script_kwargs.copy()
    ts_kwargs['help'] = 'Path to script to run as service'
    tp_kwargs = package_kwargs.copy()
    tp_kwargs['help'] = 'Package import to run as service'
    group.add_argument(*script_pargs, **ts_kwargs)
    group.add_argument(*package_pargs, **tp_kwargs)
    
    # Delete subparser
    parser_delete = subparsers.add_parser('delete', help='Delete services')
    parser_delete.set_defaults(func=utils.delete)
    group = parser_delete.add_mutually_exclusive_group(required=True)
    ts_kwargs = script_kwargs.copy()
    ts_kwargs['help'] = 'Path to service script to delete'
    tp_kwargs = package_kwargs.copy()
    tp_kwargs['help'] = 'Package import to delete service'
    group.add_argument(*script_pargs, **ts_kwargs)
    group.add_argument(*package_pargs, **tp_kwargs)
    
    # Update subparser
    parser_update = subparsers.add_parser('update', help='Update services')
    parser_update.set_defaults(func=utils.update)
    group = parser_update.add_mutually_exclusive_group(required=True)
    ts_kwargs = script_kwargs.copy()
    ts_kwargs['help'] = 'Path to service script to update'
    tp_kwargs = package_kwargs.copy()
    tp_kwargs['help'] = 'Package import to update service'
    group.add_argument(*script_pargs, **ts_kwargs)
    group.add_argument(*package_pargs, **tp_kwargs)

    cli_args = parser.parse_args()
    
    kwargs = vars(cli_args)
    func = kwargs.pop('func')
    func(**kwargs)
    
