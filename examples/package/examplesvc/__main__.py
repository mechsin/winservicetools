
import logging
import os
import sys
import threading

import examplesvc

# We manually set the name of the logger here as
# winservice because if not when everything works
# correctly the name of the module will be __main__
# which can be confusing when reviewing the logs
logger = logging.getLogger('examplesvc')

# Lets assume we are running from a virtual env here and we want to
# write the log to the file just above the virutal env folder.
logdir = os.path.join(sys.prefix, '..')

kwargs = {
          'format': '%(asctime)s\t%(levelname)s:%(process)d:%(message)s',
          'level': logging.NOTSET,
         }
logging.basicConfig(**kwargs)

event = threading.Event()
event.set()

examplesvc.main(event)
