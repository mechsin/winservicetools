
import logging
import os
import sys

import winservicetools

from examplesvc import main

# We manually set the name of the logger here as
# winservice because if not when everything works
# correctly the name of the module will be __main__
# which can be confusing when reviewing the logs
logger = logging.getLogger('winservice')

# Lets assume we are running from a virtual env here and we want to
# write the log to the file just above the virutal env folder.
logdir = os.path.join(sys.prefix, '..')

kwargs = {
          'filename': os.path.join(logdir, 'package-service.log'),
          'filemode': 'w',
          'format': '%(asctime)s\t%(name)s:%(levelname)s:%(process)d:%(message)s',
          'level': logging.NOTSET,
         }
logging.basicConfig(**kwargs)

# It is critical that you include a if name main statement and that you
# define the service class outside the if name main and that the service
# start occur in the if name main block. This is because during the service
# install this script will be imported so the service class can be interrogated
# and when the service is run the script will be run directly to start the
# service.
kwargs = {
          'target': main,
          'svc_name': 'pythonpackageservice',
          'svc_display_name': 'Python Package Service',
          'svc_description': 'Simple Python package as a Windows service',
         }

scriptservice = winservicetools.WindowsSvc.new_service(**kwargs)

if __name__ == "__main__":
    scriptservice.start()
