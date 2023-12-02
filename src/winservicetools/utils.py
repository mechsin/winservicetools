
import ctypes
import importlib
import os
import subprocess
import sys

from winservicetools import WindowsSvc

def find_service_cls(module, cls_name=None):
    """ Dark magic to find the service class

        This function takes a module object and then searches through
        it looking for a object that has a type that is type, indicating
        that it is a class and then is also a subclass of the primary
        WindowsSvc class. It returns the first item that meets this
        criteria.

        cls_name allows you to pass a cls_name that is also checked in
        case there are multiple WindowSvc classes in the same file.

    """
    for entry in dir(module):
        obj = getattr(module, entry)
        if type(obj) is type and issubclass(obj, WindowsSvc):
            if cls_name is None:
                return obj
            if cls_name == obj.__name__:
                return obj
    if cls_name:
        msg = 'No service class found with name "{}"'
        err = ValueError(msg.format(cls_name))
    else:
        msg = 'No service class found in module {}'.format(module.__name__)
        err = ValueError(msg)
    raise err

def load_module_from_path(path):
    """ Loads a module at the given path

        This code is basically lifted from the Python docs and loads
        a module dynamically from a path. This is used for the scripts
        to load the service class.
    """

    module_name = "service_module"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def get_sc_args(cls, inputstring):
    """ Return formatted arguments for sc.exe description and config """

    exe_name = cls._exe_name_ if cls._exe_name_ else sys.executable
    exe_args = cls._exe_args_ if cls._exe_args_ else tuple()
    svc_binpath = ' '.join((exe_name, *exe_args, inputstring))

    svc_name = cls._svc_name_
    # I don't understand exactly what is going on here but if you read the
    # sc.exe documentation it is very explicit that there must be a space
    # after the equals sign for each option. However when including this
    # space here subprocess does something funky and it is interpreted
    # a a literal space in front of each value. This isn't really and issue
    # except for binPath which puts a space in front of the command to execute
    # the service and will readily cause the service to fail to
    # start. So counter to official Windows documentation don't put a
    # space between the option and the value.
    binpath = 'binPath={}'.format(svc_binpath)
    displayname = 'DisplayName={}'.format(cls._svc_display_name_)

    config = [displayname]

    if cls._svc_start_:
        config.append('start={}'.format(cls._svc_start_))
    if cls._svc_depends_:
        dependslist = '/'.join(cls._svc_depends)
        config.append('depend={}'.format(dependslist))
    if cls._svc_account_:
        config.append('obj={}'.format(cls._svc_account_))
    if cls._svc_password_:
        config.append('password={}'.format(cls._svc_password_))
    if cls._svc_group_:
        config.append('group={}'.format(cls._svc_group_))

    out = {
           'name': svc_name,
           'binpath': binpath,
           'description': cls._svc_description_,
           'config': config,
          }
    return out

def process_inputs(script_path=None, import_name=None, cls_name=None):
    """ Adjudicate inputs and return the class and input string

        This function just determines if a script or import was passed
        and then ensures the correct install string is given and retrieves
        the class.

    """

    if script_path is None and import_name is None:
        raise ValueError('Must provide script path or import path')
    elif script_path and import_name:
        msg  = (
                'Please provide either a script path or a import'
                ' path not both'
               )
        raise ValueError(msg)
    elif script_path:
        # Check to make sure the script path exists because if it doesn't
        # we get a very cryptic error message.
        if not os.path.isfile(script_path):
            msg = 'Script path {} does not exist'.format(script_path)
            raise ValueError(msg)
        module = load_module_from_path(script_path)
        inputstring = script_path
    elif import_name:
        module = importlib.import_module(import_name)
        inputstring = '-m {}'.format(import_name)
    else:
        msg = (
               'There was an issue interpreting the script or import'
               ' path arguments'
              )
        raise ValueError(msg)

    cls = find_service_cls(module, cls_name)

    return cls, inputstring

def install(script_path=None, import_name=None, cls_name=None):
    """ Install and configure service using subprocess and sc.exe """

    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        raise RuntimeError('Must be admin to install services')

    cls, inputstring = process_inputs(script_path, import_name, cls_name)
    sc_args = get_sc_args(cls, inputstring)
    svc_name = sc_args['name']

    # CMD 1 creates the service
    # CMD 2 updates all the parameters of the service some of this could be
    # done during creation but I think this approach is cleaner
    # CMD 3 just sets the description which has to be done separate for some
    # reason.
    cmd1 = ('sc.exe', 'create', svc_name, sc_args['binpath'])
    cmd2 = ('sc.exe', 'config', svc_name) + tuple(sc_args['config'])
    cmd3 = ('sc.exe', 'description', svc_name, sc_args['description'])

    # We run each sub process and then check the return value and raise and
    # error if it isn't zero.
    cp = subprocess.run(cmd1)
    if cp.returncode != 0:
        raise RuntimeError('Service failed to install')

    cp = subprocess.run(cmd2)
    if cp.returncode != 0:
        raise RuntimeError('Failed to configure service')

    cp = subprocess.run(cmd3)
    if cp.returncode != 0:
        raise Warning('Service description was not set')

def delete(script_path=None, import_name=None, cls_name=None):
    """ Delete service using subprocess and sc.exe delete """

    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        raise RuntimeError('Must be admin to delete services')

    cls, inputstring = process_inputs(script_path, import_name, cls_name)
    svc_name = cls._svc_name_

    cmd1 = ('sc.exe', 'query', svc_name)
    cmd2 = ('sc.exe', 'stop', svc_name)
    cmd3 = ('sc.exe', 'delete', svc_name)

    cp = subprocess.run(cmd1, capture_output=True)
    if cp.returncode != 0:
        raise RuntimeError('Service query failed')

    if b'STOPPED' not in cp.stdout:
        cp = subprocess.run(cmd2)
        if cp.returncode != 0:
            raise RuntimeError('Unable to stop service')

    cp = subprocess.run(cmd3)
    if cp.returncode != 0:
        raise RuntimeError('Service not deleted')

def update(script_path=None, import_name=None, cls_name=None):
    """ Update service configuration using sc.exe config """

    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        raise RuntimeError('Must be admin to update services')
    
    cls, inputstring = process_inputs(script_path, import_name, cls_name)
    sc_args = get_sc_args(cls, inputstring)
    svc_name = sc_args['name']

    configargs = (sc_args['binpath'],) + tuple(sc_args['config'])
    cmd1 = ('sc.exe', 'config', svc_name) + configargs
    cmd2 = ('sc.exe', 'description', svc_name, sc_args['description'])

    cp = subprocess.run(cmd1)
    if cp.returncode != 0:
        raise RuntimeError('Failed to configure service')

    cp = subprocess.run(cmd2)
    if cp.returncode != 0:
        raise RuntimeError('Failed to update service description')
