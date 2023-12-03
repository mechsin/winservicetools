# winservicetools

Make running Python scripts and packages as Windows Services easy!

Winservicetools is a library that aims to make implementing Python scripts and packages as Windows service easy and robust. Winservicetools uses [pywin32](https:///pypi.org/project/pywin32/) under the hood but provides a single class that can generate a new service class with a few bits of meta data and a target function to run. Winservicetools also provides a command line install tool that uses the Windows ``sc.exe create`` command via subprocess to install and update services. This also provides a better view of service processes from the Task Manger Details view.

## Audience

Ever wanted to run a Python script or package as a Windows Service? You probably searched around and found that pywin32 supports this and then copied and pasted an example of a subclass of the  `wins32serviceutil.ServiceFramework` you found somewhere on the internet, made some changes, and if you are lucky, everything worked and you never looked back. But if you weren't lucky, spent hours debugging until something finally worked or you gave up. Not an ideal developer experience. It gets even worse if you want to implement another service. You copy all this cryptic boiler plate code that you just hope never breaks.

If the above sounds like you, then you're in luck because the **winservicetools** package aims to reduce the complication of implementing Python scripts and packages as Windows Services and reduces the boiler plate code to a minimum.

## How does it work

**winservicetools** still uses pywin32, and the ServiceFramework class under the hood, but all the boiler plate code needed to make the ServiceFramework class work is hidden away. winservicetools provides similar class `WindowsSvc` that can be used directly to generate a Windows Service class using the `new_service` class method, or it can be subclassed to allow for more control over how the service is run.

**winservicetools** doesn't use pywin32 PythonService.exe, although you can still choose to use it. Instead the `utils` submodule provides `install`, `delete` and `update` commands that use the Windows `sc.exe` command directly via subprocess. These commands executed from the command line via the `winservicetools.exe` that allows you manage your service based on the class meta data.

## Quick Start

You can get a Python function up and running as a Windows service in as few as 20 lines of code see the abbreviated example below or see more complete examples in the [examples folder](https://github.com/mechsin/winservicetools/tree/main/examples) in the repo.

```
import threading
import time

import winservicetools

def main(service_event: threading.Event):
    while service_event.is_set():
        time.sleep(1)

kwargs = {
          'target': main,
          'svc_name': 'pythonscriptservice',
          'svc_display_name': 'Python Script Service',
          'svc_description': 'Simple Python script as a Windows service',
         }

scriptservice = winservicetools.WindowsSvc.new_service(**kwargs)

if __name__ == "__main__":
    scriptservice.start()
```

You would then run the following command from an **elevated** `CMD.exe` or `PowerShell` **Administrator** prompt to install the service.

`winservicetools.exe install --script C:\path\to\script.py`

That's it you should now see a service in the **Service App** (`services.msc`) called *Python Script Service*.

That is pretty simple but lets break down some of the more important lines from that script in the sections below.

## Target Function

The first important note is that any function that you want to act as a target for a Windows service must accept an argument `service_event`. This argument will be passed a `threading.Event` that is in a **set** state. This event allows the service to signal to the target process when the service is asked to stop. When a service stop event is received from Windows the `WindowsSvc` base class will clear the `service_event` indicating to the target process that it should stop. This can be seen in the main function, the while loop will run as long as the `service_event.is_set()` call returns `True`, as soon as the event is cleared `service_event.ist_set()` will be `False` the while loop will exit and the service will shut down.

## Class creation

The core of the Windows service framework is the `WindowsSvc` class. Unlike most classes you deal with in Python we are never going to actually initialize this class in any of our code. The `WindowsSvc` class provides a class method called `new_service` that provides a way to generate your service class with the least amount of work. To generate a service class you must provide three things

1. Target Function (target)
2. The name of the service (svc_name)
3. The display name of the service (svc_display_name)

Optionally you can provide service description. It is recommended to always provide a description because even small amounts of documentation are good.

4. A description of the service (svc_description)

You pass these arguments all to the `new_service` method and this generates a new class that is a subclass of the `WindowsSvc` with your parameters. There are additional arguments that can be passed as well they are explained below. Many of the arguments are passed through to `sc.exe create` call so you can also find additional information in Microsoft's [sc.exe create documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-create).

The `new_service` method returns a new subclass of `WindowSvc` with all your meta data parameters programmed in. The `WindowSvc` is designed with the Python Threading class as inspiration. The `new_service` method takes a *target* argument, and a `start` method like the Python Threading class.

### Additional Arguments

Unless otherwise noted

**svc_depends**: List of service names or groups that must start before this service. The list will be formated for and passed to the `depend=` parameter of the `sc.exe create` call. See [sc.exe create documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-create) for additional detail.

**svc_start**: Specifies the start type for the service. Takes string values such as `'boot'`, `'system'`, and `'auto'`. By default nothing is passed to `sc.exe create`. Most users will want to set this value to `'auto'`. The value given is passed the `sc.exe create` `start=` parameter. See [sc.exe create documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-create) for additional detail.

**svc_account**: Specifies a name of an account in which a service will run. The value given is passed the `sc.exe create` `obj=` parameter. See [sc.exe create documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-create) for additional detail.

**svc_password**: Specifies a password. This is required if an account other than the LocalSystem account is used. The value given is passed the `sc.exe create` `password=` parameter. See [sc.exe create documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-create) for additional detail.

**svc_group**: Specifies the name of the group of which this service is a member. The value given is passed the `sc.exe create` `group=` parameter. See [sc.exe create documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-create) for additional detail.

**exe_name**: This allows you to modify the Python executable used to execute the service at run time. If nothing is passed the value of `sys.executable` at install time is used. The use of this parameter is not recommended.

**exe_args**: This allows you to pass arguments to the Python executable. Arguments should be passed as a list, tuple or other expandable iterable.

## Start method and if __name__ == '__main__'

The call to `start` method has to be protected by an if name main statement as show at the bottom of the example. This is required because the module will be imported as part of the service install process. If the service tries to start as part of the install process the import of the module will fail and the `winservicetools.exe` will be unable to install the service. It is that simple.

## Installing the service

The service is installed by the `winservicetools.exe`. You can still you pywin32 `PythonService.exe` see the [Using PythonService.exe instead](#Using `PythonService.exe` instead) section. The `winservicetools.exe` can install either a Python script or package as a service. The example is for a Python script but the exact same file would work for a package as long as it is on the Python import path. To install a package you would use the following line

`winservicetools.exe install --import yourpackage`

The [package](https://github.com/mechsin/winservicetools/tree/main/examples/package) example folder contains and example of a simple Windows service package.

If the the package isn't on the Python path then when you run the install you will see an error message similar to

`ModuleNotFoundError: No module named 'yourpackage'`

If you see this it your package isn't on the Python search path go back an make sure your package installed correctly and that you can `import` it from the Python prompt.

For more help at the command line run `winservicetools.exe --help`


### Using `PythonService.exe` instead

If you still want use `PythonService.exe` to install and control you service you can. You just need to add the `if len(sys.argv) == 1` block that is commonly found in most of the pywin32 examples. The block should look similar to the below example


```
if __name__ == "__main__":
    if len(sys.argv) == 1:
        scriptservice.start()
    else:
        win32serviceutil.HandleCommandLine(scriptservice)
```
