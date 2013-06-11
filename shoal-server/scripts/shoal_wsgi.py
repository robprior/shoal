"""
   Use this script with Apache mod_wsgi.
   If Memcached URL is defined in config you will need to run the monitor.py script as a background process seperate from this script.
"""
import os, sys, logging
from shoal_server import config, shoal

config.setup()
# change working directory so webpy static files load correctly.
try:
    os.chdir(config.shoal_dir)
except OSError as e:
    print "{0} doesn't seem to exist. Please set `shoal_dir` in shoal-server config file to the location of the shoal-server static files.".format(config.shoal_dir)
    sys.exit(1)

#If not using memcache start the monitor thread.
if not config.memcache:
    monitor_thread = shoal.ThreadMonitor()
    monitor_thread.daemon = True
    monitor_thread.start()

webpy_app = shoal.WebpyServer()
application = webpy_app.wsgi()
