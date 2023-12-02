
""" Simple example script to show how to setup a script as a Windows service """

from datetime import datetime
import logging
import os
import threading
import time

import winserviceutils

logger = logging.getLogger(__name__)

here = os.path.dirname(__file__) if os.path.dirname(__file__) else os.getcwd()

kwargs = {
          'filename': os.path.join(here, 'script-service.log'),
          'filemode': 'w',
          'format': '%(asctime)s\t%(levelname)s:%(process)d:%(message)s',
          'level': logging.NOTSET,
         }
logging.basicConfig(**kwargs)

def main(service_event: threading.Event):
    """ Simple script function that logs the time every two seconds """

    while service_event.is_set():
        dtstr = datetime.now().isoformat()
        logger.info('The current time is {}'.format(dtstr))
        time.sleep(2)

# It is critical that you include a if name main statement and that you
# define the service class prior to the if name main and that the service
# start occur in the if name main block. This is because during the service
# install this script will be imported so the service class can be interrogated
# and when the service is run the script will be run directly to start the 
# service
kwargs = {
          'target': main,
          'svc_name': 'pythonscriptservice',
          'svc_display_name': 'Python Script Service',
          'svc_description': 'Simple Python script as a Windows service',
         }

scriptservice = winserviceutils.WindowsSvc.new_service(**kwargs)

if __name__ == "__main__":
    scriptservice.start()