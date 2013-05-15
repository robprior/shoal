"""
   Use this script if running Shoal Server with Memcached.
   This script will start the RabbitMQ and ShoalUpdate Threads which will keep the list of active Squids up-to-date.
   Only 1 instance of this script needs to be running per Shoal Server.
"""
import os, sys, logging
from shoal_server import config, shoal
from time import sleep

config.setup()
monitor_thread = shoal.ThreadMonitor()
monitor_thread.daemon = True
monitor_thread.start()

try:
    while True:
        if not monitor_thread.is_alive():
            sys.exit(1)
        sleep(1)
except KeyboardInterrupt:
    sys.exit()
