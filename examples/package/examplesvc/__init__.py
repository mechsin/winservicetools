
""" Simple example script to show how to setup a script as a Windows service """

from datetime import datetime
import logging
import os
import threading
import time

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

def main(service_event: threading.Event):
    """ Simple script function that logs the time every two seconds """

    while service_event.is_set():
        dtstr = datetime.now().isoformat()
        logger.info('The current time is {}'.format(dtstr))
        time.sleep(2)
