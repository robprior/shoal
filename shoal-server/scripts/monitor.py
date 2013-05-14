import logging
import sys
import os

from shoal_server import config as config
config.setup()

from shoal_server import shoal as shoal
from threading import Thread
from time import sleep

DIRECTORY = config.shoal_dir
LOG_FILE = config.log_file
LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s] - %(message)s'

threads = []
shoal_list = {}

monitor_thread = shoal.ThreadMonitor()
monitor_thread.daemon = True
monitor_thread.start()

while True:
    if not monitor_thread.is_alive():
        sys.exit(1)
    sleep(1)
