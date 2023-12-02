
import logging
import threading
import traceback

import win32serviceutil
import win32service
import win32event
import servicemanager

from .__version__ import __version__

logger = logging.getLogger(__name__)

class WindowsSvc(win32serviceutil.ServiceFramework):

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        self.service_event = threading.Event()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        logger.info('Stop event received')
        logger.debug('Clearing run event')
        self.service_event.clear()
        logger.debug('Run event cleared')
        # This call blocks so you need to run any shutdown code before
        # calling this
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        logger.info('Service target starting')
        pargs = (
                 servicemanager.EVENTLOG_INFORMATION_TYPE,
                 servicemanager.PYS_SERVICE_STARTED,
                 (self._svc_name_,''),
                )
        servicemanager.LogMsg(*pargs)
        try:
            logger.debug('Set service event')
            self.service_event.set()
            logger.debug('Service event is set')
            logger.debug('Start target')
            logger.debug('Target positional arguments: %s', self.target_args)
            logger.debug('Target keyword arguments: %s', self.target_kwargs)
            self.target(*self.target_args, service_event=self.service_event, **self.target_kwargs)
        except Exception:
            # Catch all exceptions and log to both the Python logger
            # and log it to the Windows event log.
            logger.exception('Exception in target')
            servicemanager.LogErrorMsg(traceback.format_exc())

        pargs = (
                 servicemanager.EVENTLOG_INFORMATION_TYPE,
                 servicemanager.PYS_SERVICE_STOPPED,
                 (self._svc_name_, ''),
                )
        servicemanager.LogMsg(*pargs)
        logger.info('Target has exited service is shutting down')

    @classmethod
    def start(cls):
        """ Starts service """

        logger.info('Python windows service %s starting', cls.__name__)
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(cls)
        servicemanager.StartServiceCtrlDispatcher()
        logger.info('Python Windows Service %s stopped', cls.__name__)

    @classmethod
    def new_service(cls, target, svc_name, svc_display_name,
                    svc_description=None, svc_depends=None, svc_start='auto',
                    svc_account=None, svc_password=None, svc_group=None,
                    exe_name=None, exe_args=None, cls_name=None, target_args=(),
                    target_kwargs=None):
        """ Generate new generic Windows service class """

        kwargs = {}

        # Setup Windows service arguments
        kwargs['_svc_name_'] = svc_name
        kwargs['_svc_display_name_'] = svc_display_name
        kwargs['_svc_description_'] = svc_description
        kwargs['_svc_depends_'] = svc_depends
        kwargs['_svc_start_'] = svc_start
        kwargs['_svc_account_'] = svc_account
        kwargs['_svc_password_'] = svc_password
        kwargs['_svc_group_'] = svc_group
        kwargs['_exe_name_'] = exe_name
        kwargs['_exe_args_'] = exe_args

        # Setup target and target arguments
        # We call static method here on target other wise it will get
        # passed the class implicitly
        kwargs['target'] = staticmethod(target)
        kwargs['target_args'] = target_args
        kwargs['target_kwargs'] = target_kwargs if target_kwargs else {}

        # If class name isn't give just use the service name
        if cls_name is None:
            cls_name = svc_name

        # Make a call to type to generate a new object with the given input
        # All the keyword arguments passed will be
        obj = type(cls_name, (cls,), kwargs)

        return obj

    @classmethod
    def install(cls, scriptpath=None, modulepath=None):

        import sys
        import subprocess

        if scriptpath is None and modulepath is None:
            raise ValueError('Must provide script path or module path')
        elif scriptpath and modulepath:
            msg  = (
                    'Please provide either a script path or a module'
                    ' path not both'
                   )
            raise ValueError(msg)
        elif scriptpath:
            inputstring = scriptpath
        elif modulepath:
            inputstring = '-m {}'.format(modulepath)
        else:
            msg = (
                   'There was an issue interpeting the script and module'
                   ' path arguments'
                  )
            raise ValueError(msg)

        pythonexe = sys.executable
        svc_execution_str = "{pythonexe:} {inputstring:}"
        kwargs = {
                  'pythonexe': pythonexe,
                  'inputstring': inputstring
                 }
        svc_execution_cmd = svc_execution_str.format(**kwargs)

        svc_name = cls._svc_name_
        binpath = 'binPath= {}'.format(svc_execution_cmd)
        displayname = 'DisplayName= {}'.format(cls._svc_display_name_)

        # CMD 1 creates the service and CMD2 adds the description
        # you can't add a description until the command is created
        cmd1 = (
                'sc.exe', 'create', svc_name,
                binpath,
                displayname,
                # 'start= auto'
               )
        cmd2 = ('sc.exe', 'descrption', svc_name, cls._svc_description_)

        cp = subprocess.run(cmd1)
        if cp.returncode != 0:
            raise RuntimeError('Service failed to install')

        cp = subprocess.run(cmd2)
        if cp.returncode != 0:
            raise Warning('Service description was not set')

    @classmethod
    def delete(cls):

        import subprocess

        cmd1 = ('sc.exe', 'query', cls._svc_name_)
        cmd2 = ('sc.exe', 'stop', cls._svc_name_)
        cmd3 = ('sc.exe', 'delete', cls._svc_name_)

        cp = subprocess.run(cmd1, capture_output=True)
        if cp.returncode != 0:
            raise RuntimeError('Service query failed')
        breakpoint()

        cp = subprocess.run(cmd2)
        if cp.returncode != 0:
            raise RuntimeError('Service not deleted')



if __name__ == '__main__':

    kwargs = {}
    kwargs['svc_name'] = 'testservice'
    kwargs['svc_display_name'] = 'testservice'
    kwargs['svc_description'] = 'Python test service'
    kwargs['svc_depends'] = None
    kwargs['exe_name'] = None
    kwargs['exe_args'] = None
    testservice = WindowsSvc.new_service(**kwargs)